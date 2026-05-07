/**
 * "Run As" combined identity options.
 *
 * Each option sets trustTier + userId + requesterProfile in one click.
 * This is the primary mental model for the demo:
 *   - Scenario = what the user asks
 *   - Run As   = who is asking
 *   - Advanced = manual override
 *
 * Option ids are designed to match scenario suggested_profile_id so we can
 * map scenario.suggested_profile_id + suggested_trust_tier → a Run As option.
 */
import { findProfile } from './profiles'

export const RUN_AS_OPTIONS = [
  // ── Blue identities ────────────────────────────────────────────────────────
  {
    id: 'blue_standard',
    label: 'Standard Employee',
    sublabel: 'EMP-2011 · General',
    tier: 'blue',
    userId: 'EMP-2011',
    profileId: 'standard_employee',
  },
  {
    id: 'blue_marketing',
    label: 'Marketing Employee',
    sublabel: 'EMP-1500 · Marketing',
    tier: 'blue',
    userId: 'EMP-1500',
    profileId: 'marketing_employee',
  },
  {
    id: 'blue_jessica_park',
    label: 'Jessica Park',
    sublabel: 'EMP-2200 · Engineering',
    tier: 'blue',
    userId: 'EMP-2200',
    profileId: 'jessica_park',
  },
  {
    id: 'blue_david_kim',
    label: 'David Kim',
    sublabel: 'EMP-1043 · Engineering Manager',
    tier: 'blue',
    userId: 'EMP-1043',
    profileId: 'david_kim',
  },
  {
    id: 'blue_sarah_chen',
    label: 'Sarah Chen',
    sublabel: 'EMP-1042 · Engineering',
    tier: 'blue',
    userId: 'EMP-1042',
    profileId: 'sarah_chen',
  },
  {
    id: 'blue_devops',
    label: 'DevOps Employee',
    sublabel: 'EMP-4010 · DevOps',
    tier: 'blue',
    userId: 'EMP-4010',
    profileId: 'devops_employee',
  },
  {
    id: 'blue_sales',
    label: 'Sales Employee',
    sublabel: 'EMP-5500 · Sales',
    tier: 'blue',
    userId: 'EMP-5500',
    profileId: 'sales_employee',
  },
  // ── Grey identities ────────────────────────────────────────────────────────
  {
    id: 'grey_legal',
    label: 'Legal Claimant',
    sublabel: 'EMP-0099 · Legal (unverified)',
    tier: 'grey',
    userId: 'EMP-0099',
    profileId: 'grey_legal_claimant',
  },
  {
    id: 'grey_finance',
    label: 'Finance Claimant',
    sublabel: 'EMP-0099 · Finance (unverified)',
    tier: 'grey',
    userId: 'EMP-0099',
    profileId: 'grey_finance_claimant',
  },
  {
    id: 'grey_engineering',
    label: 'Engineering Claimant',
    sublabel: 'EMP-0099 · Engineering (unverified)',
    tier: 'grey',
    userId: 'EMP-0099',
    profileId: 'grey_engineering_claimant',
  },
  // ── Red identities ─────────────────────────────────────────────────────────
  {
    id: 'red_untrusted',
    label: 'Untrusted User',
    sublabel: 'EMP-9999 · Unverified',
    tier: 'red',
    userId: 'EMP-9999',
    profileId: 'red_untrusted',
  },
  // ── Custom ─────────────────────────────────────────────────────────────────
  {
    id: 'custom',
    label: 'Custom',
    sublabel: 'Configure in Advanced Overrides',
    tier: null,
    userId: null,
    profileId: null,
  },
]

/** Tier group definitions for rendering */
export const TIER_GROUPS = [
  { tier: 'blue',   label: '🔵 Blue',  optionIds: ['blue_standard', 'blue_marketing', 'blue_jessica_park', 'blue_david_kim', 'blue_sarah_chen', 'blue_devops', 'blue_sales'] },
  { tier: 'grey',   label: '⚪ Grey',  optionIds: ['grey_legal', 'grey_finance', 'grey_engineering'] },
  { tier: 'red',    label: '🔴 Red',   optionIds: ['red_untrusted'] },
  { tier: null,     label: '⚙️',       optionIds: ['custom'] },
]

/** Look up a Run As option by id */
export function findRunAs(id) {
  return RUN_AS_OPTIONS.find(o => o.id === id)
}

/**
 * Find the best Run As option matching a scenario's suggested context.
 * Matches on profileId + tier first, then falls back to profileId-only.
 */
export function findRunAsForSuggested(profileId, tier) {
  // Map scenario profile ids to Run As option ids
  const PROFILE_TO_RUNAS = {
    standard_employee:        'blue_standard',
    marketing_employee:       'blue_marketing',
    jessica_park:             'blue_jessica_park',
    david_kim:                'blue_david_kim',
    sarah_chen:               'blue_sarah_chen',
    devops_employee:          'blue_devops',
    sales_employee:           'blue_sales',
    grey_legal_claimant:      'grey_legal',
    grey_finance_claimant:    'grey_finance',
    grey_engineering_claimant:'grey_engineering',
    red_untrusted:            'red_untrusted',
  }
  const runAsId = PROFILE_TO_RUNAS[profileId]
  return runAsId ? findRunAs(runAsId) : null
}

/** Resolve the effective (tier, userId, profileData) from a runAs + optional overrides */
export function resolveEffective(runAsId, advTier, advUserId, advProfileId) {
  const runAs = findRunAs(runAsId)
  const tier      = advTier      || runAs?.tier    || 'blue'
  const userId    = advUserId    || runAs?.userId   || 'EMP-2200'
  const profileId = advProfileId || runAs?.profileId || 'jessica_park'
  const profile   = findProfile(profileId)?.data || null
  return { tier, userId, profileId, profile }
}
