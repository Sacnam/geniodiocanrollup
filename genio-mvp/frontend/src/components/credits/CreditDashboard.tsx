/**
 * Credit Dashboard Components for Genio Knowledge OS.
 * 
 * This module provides React components for:
 * - Credit balance display
 * - Credit package purchase
 * - Transaction history
 * - Usage statistics
 * - Streak and referral displays
 */

import React from 'react';
import { useWalletStatus, useCreditPackages, usePurchaseCredits, useTransactions, useUsageStats } from '../../services/credits';
import { CreditPackage, STREAK_MILESTONES, OPERATION_LABELS } from '../../types/credits';

// ==================== Credit Balance Display ====================

export function CreditBalance({
    balance,
    monthlyAllocation,
    hasLowBalance,
    isExhausted,
    onPurchaseClick
}: {
    balance: number;
    monthlyAllocation: number;
    hasLowBalance: boolean;
    isExhausted: boolean;
    onPurchaseClick: () => void;
}) {
    const percentage = Math.min(100, (balance / monthlyAllocation) * 100);

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Genio Credits</h3>
                <span className={`text-2xl font-bold ${isExhausted ? 'text-red-600' : hasLowBalance ? 'text-yellow-600' : 'text-green-600'}`}>
                    {balance.toLocaleString()} GC
                </span>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
                <div
                    className={`h-2.5 rounded-full transition-all ${isExhausted ? 'bg-red-500' : hasLowBalance ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                    style={{ width: `${percentage}%` }}
                />
            </div>

            {/* Status message */}
            {isExhausted && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
                    <p className="text-sm text-red-700">
                        ⚠️ Your credits are exhausted. Purchase more to continue using AI features.
                    </p>
                </div>
            )}

            {hasLowBalance && !isExhausted && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
                    <p className="text-sm text-yellow-700">
                        ⚡ Running low on credits. Consider purchasing more.
                    </p>
                </div>
            )}

            <button
                onClick={onPurchaseClick}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
                Buy Credits
            </button>
        </div>
    );
}

// ==================== Credit Package Card ====================

export function CreditPackageCard({
    pkg,
    isPopular = false,
    onSelect
}: {
    pkg: {
        id: string;
        name: string;
        credits: number;
        bonus_credits: number;
        price_cents: number;
        price_formatted: string;
        features_unlocked: string[];
        validity_days: number;
    };
    isPopular?: boolean;
    onSelect: () => void;
}) {
    const totalCredits = pkg.credits + pkg.bonus_credits;

    return (
        <div className={`relative bg-white rounded-lg shadow-md p-6 ${isPopular ? 'ring-2 ring-indigo-500' : ''}`}>
            {isPopular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-indigo-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                        MOST POPULAR
                    </span>
                </div>
            )}

            <h4 className="text-lg font-semibold text-gray-900 mb-2">{pkg.name}</h4>

            <div className="mb-4">
                <span className="text-3xl font-bold text-gray-900">{pkg.price_formatted}</span>
            </div>

            <div className="mb-4">
                <p className="text-2xl font-bold text-indigo-600">
                    {totalCredits.toLocaleString()} credits
                </p>
                {pkg.bonus_credits > 0 && (
                    <p className="text-sm text-green-600">
                        +{pkg.bonus_credits.toLocaleString()} bonus credits
                    </p>
                )}
            </div>

            <ul className="text-sm text-gray-600 mb-6 space-y-2">
                <li>✓ Valid for {pkg.validity_days} days</li>
                {pkg.features_unlocked.map((feature, idx) => (
                    <li key={idx}>✓ {feature}</li>
                ))}
            </ul>

            <button
                onClick={onSelect}
                className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${isPopular
                    ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
                    }`}
            >
                Select {pkg.name}
            </button>
        </div>
    );
}

// ==================== Purchase Modal ====================

export function PurchaseModal({
    isOpen,
    onClose
}: {
    isOpen: boolean;
    onClose: () => void;
}) {
    const { data: packages, isLoading } = useCreditPackages();
    const purchaseMutation = usePurchaseCredits();

    const handlePurchase = async (pkgId: string) => {
        try {
            const result = await purchaseMutation.mutateAsync({
                pkg: pkgId as CreditPackage,
                successUrl: `${window.location.origin}/credits?success=true`,
                cancelUrl: `${window.location.origin}/credits?canceled=true`,
            });

            // Redirect to Stripe checkout
            window.location.href = result.url;
        } catch (error) {
            console.error('Purchase failed:', error);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                <div className="p-6 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                        <h2 className="text-2xl font-bold text-gray-900">Purchase Credits</h2>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <p className="text-gray-600 mt-2">
                        Choose a credit package that fits your needs. Credits never expire for 12 months.
                    </p>
                </div>

                <div className="p-6">
                    {isLoading ? (
                        <div className="text-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                            <p className="mt-4 text-gray-600">Loading packages...</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {packages?.map((pkg, idx) => (
                                <CreditPackageCard
                                    key={pkg.id}
                                    pkg={pkg}
                                    isPopular={pkg.id === 'pro'}
                                    onSelect={() => handlePurchase(pkg.id)}
                                />
                            ))}
                        </div>
                    )}
                </div>

                <div className="p-6 bg-gray-50 border-t border-gray-200">
                    <p className="text-sm text-gray-500 text-center">
                        Secure payment powered by Stripe. Credits are added to your account immediately after purchase.
                    </p>
                </div>
            </div>
        </div>
    );
}

// ==================== Transaction List ====================

export function TransactionList({
    transactions,
    isLoading
}: {
    transactions: Array<{
        id: number;
        type: string;
        operation: string | null;
        amount: number;
        balance_after: number;
        description: string | null;
        created_at: string;
    }>;
    isLoading: boolean;
}) {
    if (isLoading) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <div className="animate-pulse space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-12 bg-gray-200 rounded"></div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Transaction History</h3>
            </div>

            <div className="divide-y divide-gray-200">
                {transactions.length === 0 ? (
                    <div className="p-6 text-center text-gray-500">
                        No transactions yet
                    </div>
                ) : (
                    transactions.map((tx) => (
                        <div key={tx.id} className="p-4 hover:bg-gray-50">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="font-medium text-gray-900">
                                        {tx.description || tx.type.replace(/_/g, ' ')}
                                    </p>
                                    <p className="text-sm text-gray-500">
                                        {new Date(tx.created_at).toLocaleDateString()} at{' '}
                                        {new Date(tx.created_at).toLocaleTimeString()}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className={`font-semibold ${tx.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {tx.amount >= 0 ? '+' : ''}{tx.amount} GC
                                    </p>
                                    <p className="text-sm text-gray-500">
                                        Balance: {tx.balance_after} GC
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

// ==================== Usage Chart ====================

export function UsageChart({ stats }: {
    stats: {
        period_days: number;
        total_spent: number;
        total_earned: number;
        net_change: number;
        by_operation: Record<string, { count: number; credits: number }>;
        average_daily_spend: number;
        projected_monthly_spend: number;
    }
}) {
    const operations = Object.entries(stats.by_operation)
        .sort((a, b) => b[1].credits - a[1].credits)
        .slice(0, 5);

    const maxCredits = Math.max(...operations.map(([, data]) => data.credits), 1);

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Usage (Last {stats.period_days} days)
            </h3>

            <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center">
                    <p className="text-2xl font-bold text-red-600">{stats.total_spent}</p>
                    <p className="text-sm text-gray-500">Credits Spent</p>
                </div>
                <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">{stats.total_earned}</p>
                    <p className="text-sm text-gray-500">Credits Earned</p>
                </div>
                <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">
                        {stats.net_change >= 0 ? '+' : ''}{stats.net_change}
                    </p>
                    <p className="text-sm text-gray-500">Net Change</p>
                </div>
            </div>

            {/* Bar chart for operations */}
            <div className="space-y-3">
                {operations.map(([op, data]) => (
                    <div key={op}>
                        <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-gray-600">
                                {OPERATION_LABELS[op as keyof typeof OPERATION_LABELS] || op}
                            </span>
                            <span className="font-medium">{data.credits} GC</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                                className="bg-indigo-500 h-2 rounded-full"
                                style={{ width: `${(data.credits / maxCredits) * 100}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-6 pt-4 border-t border-gray-200">
                <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Avg. daily spend:</span>
                    <span className="font-medium">{stats.average_daily_spend.toFixed(1)} GC</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                    <span className="text-gray-500">Projected monthly:</span>
                    <span className="font-medium">{stats.projected_monthly_spend.toFixed(0)} GC</span>
                </div>
            </div>
        </div>
    );
}

// ==================== Streak Display ====================

export function StreakDisplay({
    currentStreak,
    longestStreak
}: {
    currentStreak: number;
    longestStreak: number;
}) {
    const nextMilestone = STREAK_MILESTONES.find(m => m.days > currentStreak);

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Streak 🔥</h3>

            <div className="flex items-center justify-center mb-4">
                <div className="text-center">
                    <p className="text-5xl font-bold text-orange-500">{currentStreak}</p>
                    <p className="text-gray-600">days</p>
                </div>
            </div>

            <div className="flex justify-center gap-2 mb-4">
                {STREAK_MILESTONES.map((milestone) => (
                    <div
                        key={milestone.days}
                        className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${currentStreak >= milestone.days
                            ? 'bg-orange-500 text-white'
                            : 'bg-gray-200 text-gray-500'
                            }`}
                        title={`${milestone.label}: +${milestone.bonus} GC bonus`}
                    >
                        {milestone.days}
                    </div>
                ))}
            </div>

            {nextMilestone && (
                <p className="text-center text-sm text-gray-500">
                    {nextMilestone.days - currentStreak} more days until +{nextMilestone.bonus} GC bonus!
                </p>
            )}

            <p className="text-center text-xs text-gray-400 mt-2">
                Longest streak: {longestStreak} days
            </p>
        </div>
    );
}

// ==================== Referral Card ====================

export function ReferralCard({
    referralCode,
    referralCreditsEarned,
    onCopyCode
}: {
    referralCode: string;
    referralCreditsEarned: number;
    onCopyCode: () => void;
}) {
    return (
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg shadow p-6 text-white">
            <h3 className="text-lg font-semibold mb-2">Invite Friends 🎁</h3>
            <p className="text-sm opacity-90 mb-4">
                Share your referral code and earn 100 GC when they make their first purchase!
            </p>

            <div className="bg-white/20 rounded-md p-3 flex items-center justify-between mb-4">
                <code className="text-lg font-mono">{referralCode}</code>
                <button
                    onClick={onCopyCode}
                    className="ml-2 p-2 hover:bg-white/20 rounded transition-colors"
                    title="Copy code"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                </button>
            </div>

            <p className="text-sm opacity-90">
                You've earned <span className="font-bold">{referralCreditsEarned} GC</span> from referrals!
            </p>
        </div>
    );
}

// ==================== Main Dashboard ====================

export function CreditDashboard() {
    const [showPurchase, setShowPurchase] = React.useState(false);
    const { data: wallet, isLoading: walletLoading } = useWalletStatus();
    const { data: transactions, isLoading: txLoading } = useTransactions(10);
    const { data: stats } = useUsageStats(30);

    const handleCopyReferralCode = () => {
        if (wallet?.referral_code) {
            navigator.clipboard.writeText(wallet.referral_code);
        }
    };

    if (walletLoading) {
        return (
            <div className="animate-pulse space-y-4 p-6">
                <div className="h-32 bg-gray-200 rounded-lg"></div>
                <div className="h-64 bg-gray-200 rounded-lg"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Top row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {wallet && (
                    <>
                        <CreditBalance
                            balance={wallet.balance}
                            monthlyAllocation={wallet.monthly_allocation}
                            hasLowBalance={wallet.has_low_balance}
                            isExhausted={wallet.is_exhausted}
                            onPurchaseClick={() => setShowPurchase(true)}
                        />

                        <StreakDisplay
                            currentStreak={wallet.current_streak}
                            longestStreak={wallet.longest_streak}
                        />

                        <ReferralCard
                            referralCode={wallet.referral_code}
                            referralCreditsEarned={wallet.referral_credits_earned}
                            onCopyCode={handleCopyReferralCode}
                        />
                    </>
                )}
            </div>

            {/* Bottom row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {stats && <UsageChart stats={stats} />}
                <TransactionList transactions={transactions || []} isLoading={txLoading} />
            </div>

            {/* Purchase Modal */}
            <PurchaseModal
                isOpen={showPurchase}
                onClose={() => setShowPurchase(false)}
            />
        </div>
    );
}

export default CreditDashboard;
