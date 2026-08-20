import React, { useState } from 'react';
import axios from 'axios';
import { 
  CreditCard, ShieldCheck, Lock, CheckCircle2, 
  X, RefreshCw, Sparkles, DollarSign 
} from 'lucide-react';

interface Course {
  id: string;
  code: string;
  title: string;
  price: number;
  description?: string;
}

interface CheckoutModalProps {
  course: Course | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CheckoutModal: React.FC<CheckoutModalProps> = ({
  course,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [processing, setProcessing] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<'credit_card' | 'paypal' | 'stripe'>('credit_card');
  const [cardNumber, setCardNumber] = useState('4242 •••• •••• 4242');
  const [expiry, setExpiry] = useState('12/28');
  const [cvc, setCvc] = useState('888');

  if (!isOpen || !course) return null;

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    if (processing) return;

    setProcessing(true);

    try {
      const token = localStorage.getItem('token');
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'https://ai-doubt-backend.onrender.com';

      await axios.post(
        `${backendUrl}/api/v1/payments/checkout`,
        {
          course_id: course.id,
          amount: course.price,
          currency: 'USD',
          payment_method: paymentMethod
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setProcessing(false);
      onSuccess();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Payment processing failed');
      setProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 rounded-xl">
              <CreditCard className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-1.5">
                Secure Checkout Gateway
                <Lock className="w-3.5 h-3.5 text-emerald-400" />
              </h3>
              <p className="text-xs text-slate-400">256-bit SSL Encrypted Transaction</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Order Summary */}
        <div className="p-5 bg-slate-950/40 border-b border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-mono text-indigo-400 uppercase font-semibold">{course.code}</span>
            <span>Course Access Lifetime</span>
          </div>
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-white max-w-[70%] truncate">{course.title}</h4>
            <span className="text-xl font-extrabold text-emerald-400">
              {course.price === 0 ? 'Free' : `$${course.price.toFixed(2)}`}
            </span>
          </div>
        </div>

        {/* Payment Form */}
        <form onSubmit={handleCheckout} className="p-6 space-y-5">
          {/* Method Selector */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 block">Select Payment Method</label>
            <div className="grid grid-cols-3 gap-2.5">
              <button
                type="button"
                onClick={() => setPaymentMethod('credit_card')}
                className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                  paymentMethod === 'credit_card'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <CreditCard className="w-3.5 h-3.5 text-indigo-400" /> Credit Card
              </button>
              <button
                type="button"
                onClick={() => setPaymentMethod('stripe')}
                className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                  paymentMethod === 'stripe'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Stripe Pay
              </button>
              <button
                type="button"
                onClick={() => setPaymentMethod('paypal')}
                className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                  paymentMethod === 'paypal'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <DollarSign className="w-3.5 h-3.5 text-indigo-400" /> PayPal
              </button>
            </div>
          </div>

          {/* Card Simulation Inputs */}
          <div className="space-y-3 pt-1">
            <div>
              <label className="text-[11px] text-slate-400 block mb-1">Card Number</label>
              <input
                type="text"
                value={cardNumber}
                onChange={e => setCardNumber(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-mono text-slate-200 focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Expiry Date</label>
                <input
                  type="text"
                  value={expiry}
                  onChange={e => setExpiry(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-mono text-slate-200 focus:border-indigo-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">CVC Code</label>
                <input
                  type="password"
                  value={cvc}
                  onChange={e => setCvc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-mono text-slate-200 focus:border-indigo-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Security guarantee */}
          <div className="p-3 bg-emerald-950/30 border border-emerald-500/20 rounded-xl flex items-center gap-2 text-emerald-300 text-xs">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Instant enrollment activation upon payment completion.</span>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={processing}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2"
          >
            {processing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Processing Payment...
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4" /> Complete Payment & Enroll (${course.price.toFixed(2)})
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
