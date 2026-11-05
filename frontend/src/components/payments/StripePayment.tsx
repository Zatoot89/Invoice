import { useState, useEffect } from 'react';
import { loadStripe, StripeElementsOptions } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  Card,
  CardBody,
  Input,
  Checkbox,
  Spinner,
  Alert,
} from '@nextui-org/react';
import {
  CreditCardIcon,
  LockClosedIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface StripePaymentProps {
  invoice: {
    id: number;
    invoice_number: string;
    total: number;
    currency: string;
    customer_name: string;
  };
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (paymentResult: any) => void;
}

interface PaymentFormProps {
  invoice: StripePaymentProps['invoice'];
  onSuccess: (paymentResult: any) => void;
  onError: (error: string) => void;
}

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

const PaymentForm = ({ invoice, onSuccess, onError }: PaymentFormProps) => {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);
  const [clientSecret, setClientSecret] = useState<string>('');
  const [savePaymentMethod, setSavePaymentMethod] = useState(false);
  const [billingDetails, setBillingDetails] = useState({
    name: invoice.customer_name,
    email: '',
    phone: '',
  });

  useEffect(() => {
    // Create PaymentIntent when component mounts
    createPaymentIntent();
  }, []);

  const createPaymentIntent = async () => {
    try {
      const response = await fetch('/api/v1/stripe/create-payment-intent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          invoice_id: invoice.id,
          save_payment_method: savePaymentMethod,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create payment intent');
      }

      const data = await response.json();
      setClientSecret(data.client_secret);
    } catch (error) {
      console.error('PaymentIntent creation failed:', error);
      onError('Failed to initialize payment. Please try again.');
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements || !clientSecret) {
      return;
    }

    setProcessing(true);

    const cardElement = elements.getElement(CardElement);
    if (!cardElement) {
      setProcessing(false);
      return;
    }

    try {
      // Confirm the payment
      const { error, paymentIntent } = await stripe.confirmCardPayment(
        clientSecret,
        {
          payment_method: {
            card: cardElement,
            billing_details: {
              name: billingDetails.name,
              email: billingDetails.email,
              phone: billingDetails.phone,
            },
          },
        }
      );

      if (error) {
        console.error('Payment failed:', error);
        onError(error.message || 'Payment failed');
      } else if (paymentIntent.status === 'succeeded') {
        toast.success('Payment successful!');
        onSuccess(paymentIntent);
      }
    } catch (err) {
      console.error('Payment error:', err);
      onError('An unexpected error occurred');
    } finally {
      setProcessing(false);
    }
  };

  const cardElementOptions = {
    style: {
      base: {
        fontSize: '16px',
        color: '#424770',
        '::placeholder': {
          color: '#aab7c4',
        },
      },
      invalid: {
        color: '#9e2146',
      },
    },
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Invoice Summary */}
      <Card>
        <CardBody>
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold">Invoice {invoice.invoice_number}</h3>
              <p className="text-sm text-gray-600">Payment to {invoice.customer_name}</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-green-600">
                {invoice.currency} {invoice.total.toLocaleString()}
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Billing Details */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Billing Information
        </h4>
        
        <Input
          label="Full Name"
          value={billingDetails.name}
          onChange={(e) => setBillingDetails(prev => ({ ...prev, name: e.target.value }))}
          required
        />
        
        <Input
          label="Email"
          type="email"
          value={billingDetails.email}
          onChange={(e) => setBillingDetails(prev => ({ ...prev, email: e.target.value }))}
          required
        />
        
        <Input
          label="Phone (Optional)"
          type="tel"
          value={billingDetails.phone}
          onChange={(e) => setBillingDetails(prev => ({ ...prev, phone: e.target.value }))}
        />
      </div>

      {/* Card Details */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center">
          <CreditCardIcon className="h-4 w-4 mr-2" />
          Card Information
        </h4>
        
        <div className="p-3 border border-gray-300 rounded-lg focus-within:border-primary-500 dark:border-gray-600">
          <CardElement options={cardElementOptions} />
        </div>
      </div>

      {/* Save Payment Method */}
      <Checkbox
        isSelected={savePaymentMethod}
        onValueChange={setSavePaymentMethod}
      >
        Save payment method for future use
      </Checkbox>

      {/* Security Notice */}
      <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
        <LockClosedIcon className="h-4 w-4" />
        <span>Your payment information is secure and encrypted</span>
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        color="primary"
        size="lg"
        className="w-full"
        disabled={!stripe || processing || !clientSecret}
        startContent={processing ? <Spinner size="sm" /> : <CreditCardIcon className="h-5 w-5" />}
      >
        {processing ? 'Processing Payment...' : `Pay ${invoice.currency} ${invoice.total.toLocaleString()}`}
      </Button>

      {/* Powered by Stripe */}
      <div className="text-center text-xs text-gray-500">
        Powered by <span className="font-semibold">Stripe</span>
      </div>
    </form>
  );
};

export default function StripePayment({ invoice, isOpen, onClose, onSuccess }: StripePaymentProps) {
  const [error, setError] = useState<string>('');

  const handleSuccess = (paymentResult: any) => {
    onSuccess(paymentResult);
    onClose();
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
    toast.error(errorMessage);
  };

  const options: StripeElementsOptions = {
    appearance: {
      theme: 'stripe',
      variables: {
        colorPrimary: '#3b82f6',
      },
    },
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="2xl"
      classNames={{
        body: "py-6",
        header: "border-b border-gray-200 dark:border-gray-700",
      }}
      isDismissable={false}
      isKeyboardDismissDisabled={true}
    >
      <ModalContent>
        <ModalHeader className="flex flex-col gap-1">
          <h2 className="text-xl font-semibold">Secure Payment</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Complete your payment securely with Stripe
          </p>
        </ModalHeader>

        <ModalBody>
          {error && (
            <Alert
              color="danger"
              variant="faded"
              description={error}
            />
          )}

          <Elements stripe={stripePromise} options={options}>
            <PaymentForm
              invoice={invoice}
              onSuccess={handleSuccess}
              onError={handleError}
            />
          </Elements>
        </ModalBody>

        <ModalFooter>
          <Button
            variant="light"
            onPress={onClose}
            className="mr-2"
          >
            Cancel
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

// Stripe Checkout redirect option
export const StripeCheckout = {
  redirectToCheckout: async (invoice: StripePaymentProps['invoice']) => {
    try {
      const response = await fetch('/api/v1/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          invoice_id: invoice.id,
          success_url: `${window.location.origin}/invoices/${invoice.id}/payment/success`,
          cancel_url: `${window.location.origin}/invoices/${invoice.id}/payment/cancel`,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const data = await response.json();
      
      // Redirect to Stripe Checkout
      window.location.href = data.session_url;
      
    } catch (error) {
      console.error('Checkout creation failed:', error);
      toast.error('Failed to redirect to payment. Please try again.');
    }
  },
};