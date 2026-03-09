/**
 * Credit system API service.
 * 
 * Provides functions for interacting with the credit management API.
 */

import { api, WalletStatus, CreditPackageInfo, CreditTransaction, UsageStats } from './api';
import { CreditPackage } from '../types/credits';

// ==================== Wallet ====================

export async function getWalletStatus(): Promise<WalletStatus> {
    return api.getWalletStatus();
}

// ==================== Packages ====================

export async function getCreditPackages(): Promise<CreditPackageInfo[]> {
    return api.getCreditPackages();
}

export async function purchaseCredits(
    pkg: CreditPackage,
    successUrl: string,
    cancelUrl: string,
) {
    return api.purchaseCredits(pkg, successUrl, cancelUrl);
}

// ==================== Transactions ====================

export async function getTransactions(
    limit: number = 20,
    offset: number = 0,
): Promise<CreditTransaction[]> {
    return api.getCreditTransactions(limit, offset);
}

// ==================== Usage Stats ====================

export async function getUsageStats(days: number = 30): Promise<UsageStats> {
    return api.getCreditUsageStats(days);
}

// ==================== Operations ====================

export async function checkCanAfford(operation: string, quantity: number = 1) {
    return api.checkCanAfford(operation, quantity);
}

// ==================== Referrals ====================

export async function validateReferralCode(code: string) {
    return api.validateReferralCode(code);
}

// ==================== Streaks ====================

export async function recordDailyStreak() {
    return api.recordDailyStreak();
}

// ==================== React Query Hooks ====================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useWalletStatus() {
    return useQuery({
        queryKey: ['credits', 'wallet'],
        queryFn: getWalletStatus,
        staleTime: 30000, // 30 seconds
    });
}

export function useCreditPackages() {
    return useQuery({
        queryKey: ['credits', 'packages'],
        queryFn: getCreditPackages,
        staleTime: 300000, // 5 minutes
    });
}

export function useTransactions(limit: number = 20, offset: number = 0) {
    return useQuery({
        queryKey: ['credits', 'transactions', { limit, offset }],
        queryFn: () => getTransactions(limit, offset),
    });
}

export function useUsageStats(days: number = 30) {
    return useQuery({
        queryKey: ['credits', 'usage', { days }],
        queryFn: () => getUsageStats(days),
    });
}

export function usePurchaseCredits() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            pkg,
            successUrl,
            cancelUrl,
        }: {
            pkg: CreditPackage;
            successUrl: string;
            cancelUrl: string;
        }) => purchaseCredits(pkg, successUrl, cancelUrl),
        onSuccess: () => {
            // Invalidate wallet status to refresh balance
            queryClient.invalidateQueries({ queryKey: ['credits', 'wallet'] });
        },
    });
}

export function useReferralValidation(code: string | null) {
    return useQuery({
        queryKey: ['credits', 'referral', code],
        queryFn: () => validateReferralCode(code!),
        enabled: !!code,
    });
}

export function useRecordStreak() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: recordDailyStreak,
        onSuccess: () => {
            // Invalidate wallet status to refresh streak
            queryClient.invalidateQueries({ queryKey: ['credits', 'wallet'] });
        },
    });
}

// Re-export types for convenience
export type { WalletStatus, CreditPackageInfo, CreditTransaction, UsageStats };
