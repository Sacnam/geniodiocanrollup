/**
 * Credit system types for Genio Knowledge OS.
 * 
 * This module defines TypeScript types for:
 * - Credit wallet management
 * - Credit packages and purchases
 * - Transaction history
 * - Usage statistics
 */

// ==================== Enums ====================

export enum CreditOperationType {
    // LLM Operations
    BRIEF_SIMPLE = 'brief_simple',
    BRIEF_ADVANCED = 'brief_advanced',
    BRIEF_PREMIUM = 'brief_premium',
    SEARCH_SEMANTIC = 'search_semantic',
    SUMMARIZE = 'summarize',
    EXPLAIN_CONCEPT = 'explain_concept',
    FLASHCARD_GENERATE = 'flashcard_generate',
    EMBEDDING_GENERATE = 'embedding_generate',

    // TTS Operations
    TTS_PIPER = 'tts_piper',
    TTS_PLAYHT = 'tts_playht',
    TTS_ELEVENLABS = 'tts_elevenlabs',

    // Storage
    STORAGE_MB = 'storage_mb',

    // Premium Features
    EXPORT_PDF = 'export_pdf',
    TEAM_SHARE = 'team_share',
    API_CALL = 'api_call',

    // Document Operations
    DOCUMENT_UPLOAD = 'document_upload',
    DOCUMENT_OCR = 'document_ocr',
    DOCUMENT_ANALYZE = 'document_analyze',
    KNOWLEDGE_GRAPH = 'knowledge_graph',
}

export enum CreditTransactionType {
    MONTHLY_ALLOCATION = 'monthly_allocation',
    PURCHASE = 'purchase',
    REFERRAL_BONUS = 'referral_bonus',
    STREAK_BONUS = 'streak_bonus',
    ADMIN_GRANT = 'admin_grant',
    REFUND = 'refund',
    OPERATION = 'operation',
    EXPIRATION = 'expiration',
    ADMIN_DEDUCT = 'admin_deduct',
}

export enum CreditPackage {
    MINI = 'mini',
    STANDARD = 'standard',
    PRO = 'pro',
    POWER = 'power',
}

// ==================== API Response Types ====================

export interface WalletStatus {
    balance: number;
    total_earned: number;
    total_spent: number;
    monthly_allocation: number;
    allocation_resets_at: string | null;
    current_streak: number;
    longest_streak: number;
    referral_code: string;
    referral_credits_earned: number;
    has_low_balance: boolean;
    is_exhausted: boolean;
}

export interface CreditPackageInfo {
    id: string;
    name: string;
    credits: number;
    bonus_credits: number;
    price_cents: number;
    price_formatted: string;
    features_unlocked: string[];
    validity_days: number;
}

export interface CreditTransaction {
    id: number;
    type: CreditTransactionType;
    operation: CreditOperationType | null;
    amount: number;
    balance_after: number;
    description: string | null;
    created_at: string;
}

export interface UsageStats {
    period_days: number;
    total_spent: number;
    total_earned: number;
    net_change: number;
    by_operation: Record<string, { count: number; credits: number }>;
    average_daily_spend: number;
    projected_monthly_spend: number;
}

export interface OperationCost {
    operation: string;
    credits: number;
    description: string;
}

export interface ReferralValidation {
    valid: boolean;
    referrer_name: string | null;
    bonus_credits: number;
}

export interface PurchaseResponse {
    session_id: string;
    url: string;
    package: string;
    credits: number;
    bonus_credits: number;
}

export interface AffordabilityCheck {
    can_afford: boolean;
    credits_needed: number;
    current_balance: number;
}

// ==================== Component Props ====================

export interface CreditBalanceProps {
    balance: number;
    monthlyAllocation: number;
    hasLowBalance: boolean;
    isExhausted: boolean;
    onPurchaseClick: () => void;
}

export interface CreditPackageCardProps {
    package: CreditPackageInfo;
    isPopular?: boolean;
    onSelect: (pkg: CreditPackageInfo) => void;
}

export interface TransactionListProps {
    transactions: CreditTransaction[];
    isLoading: boolean;
}

export interface UsageChartProps {
    stats: UsageStats;
}

export interface StreakDisplayProps {
    currentStreak: number;
    longestStreak: number;
    lastBonus: number;
}

export interface ReferralCardProps {
    referralCode: string;
    referralCreditsEarned: number;
    onCopyCode: () => void;
}

// ==================== Constants ====================

export const CREDIT_VALUE_USD = 0.01; // 1 credit = $0.01

export const OPERATION_LABELS: Record<CreditOperationType, string> = {
    [CreditOperationType.BRIEF_SIMPLE]: 'Basic Brief',
    [CreditOperationType.BRIEF_ADVANCED]: 'Advanced Brief',
    [CreditOperationType.BRIEF_PREMIUM]: 'Premium Brief',
    [CreditOperationType.SEARCH_SEMANTIC]: 'Semantic Search',
    [CreditOperationType.SUMMARIZE]: 'Summarization',
    [CreditOperationType.EXPLAIN_CONCEPT]: 'Concept Explanation',
    [CreditOperationType.FLASHCARD_GENERATE]: 'Flashcard Generation',
    [CreditOperationType.EMBEDDING_GENERATE]: 'Embedding Generation',
    [CreditOperationType.TTS_PIPER]: 'TTS (Basic)',
    [CreditOperationType.TTS_PLAYHT]: 'TTS (Standard)',
    [CreditOperationType.TTS_ELEVENLABS]: 'TTS (Premium)',
    [CreditOperationType.STORAGE_MB]: 'Storage',
    [CreditOperationType.EXPORT_PDF]: 'PDF Export',
    [CreditOperationType.TEAM_SHARE]: 'Team Sharing',
    [CreditOperationType.API_CALL]: 'API Call',
    [CreditOperationType.DOCUMENT_UPLOAD]: 'Document Upload',
    [CreditOperationType.DOCUMENT_OCR]: 'OCR Processing',
    [CreditOperationType.DOCUMENT_ANALYZE]: 'Document Analysis',
    [CreditOperationType.KNOWLEDGE_GRAPH]: 'Knowledge Graph',
};

export const TRANSACTION_TYPE_LABELS: Record<CreditTransactionType, string> = {
    [CreditTransactionType.MONTHLY_ALLOCATION]: 'Monthly Allocation',
    [CreditTransactionType.PURCHASE]: 'Purchase',
    [CreditTransactionType.REFERRAL_BONUS]: 'Referral Bonus',
    [CreditTransactionType.STREAK_BONUS]: 'Streak Bonus',
    [CreditTransactionType.ADMIN_GRANT]: 'Admin Grant',
    [CreditTransactionType.REFUND]: 'Refund',
    [CreditTransactionType.OPERATION]: 'Operation',
    [CreditTransactionType.EXPIRATION]: 'Expiration',
    [CreditTransactionType.ADMIN_DEDUCT]: 'Admin Deduction',
};

export const STREAK_MILESTONES = [
    { days: 7, bonus: 10, label: '1 Week' },
    { days: 30, bonus: 50, label: '1 Month' },
    { days: 90, bonus: 200, label: '3 Months' },
];
