/**
 * Requester profile presets — frontend-only.
 *
 * When a profile is selected, userId updates from profile.data.employee_id
 * (unless the user typed a custom userId). Trust tier is always independent.
 *
 * Scenarios carry suggested_profile_id referencing these ids.
 */
export const PROFILES = [
  {
    id: 'standard_employee',
    label: 'Standard Employee',
    subtitle: 'Blue · General employee',
    tier_hint: 'blue',
    data: {
      employee_id: 'EMP-2011',
      name: 'Standard Employee',
      department: 'General',
      team: 'General',
      is_manager: false,
      reports: [],
    },
  },
  {
    id: 'jessica_park',
    label: 'Jessica Park',
    subtitle: 'Blue · Engineering employee',
    tier_hint: 'blue',
    data: {
      employee_id: 'EMP-2200',
      name: 'Jessica Park',
      department: 'Engineering',
      team: 'Engineering',
      is_manager: false,
      reports: [],
    },
  },
  {
    id: 'david_kim',
    label: 'David Kim',
    subtitle: 'Blue · Engineering manager',
    tier_hint: 'blue',
    data: {
      employee_id: 'EMP-1043',
      name: 'David Kim',
      department: 'Engineering',
      team: 'Engineering',
      is_manager: true,
      reports: ['Jordan Rivera', 'EMP-1044'],
    },
  },
  {
    id: 'sarah_chen',
    label: 'Sarah Chen',
    subtitle: 'Blue · Engineering employee',
    tier_hint: 'blue',
    data: {
      employee_id: 'EMP-1042',
      name: 'Sarah Chen',
      department: 'Engineering',
      team: 'Engineering',
      is_manager: false,
      reports: [],
    },
  },
  {
    id: 'marketing_employee',
    label: 'Marketing Employee',
    subtitle: 'Blue · Marketing',
    tier_hint: 'blue',
    data: {
      employee_id: 'EMP-1500',
      name: 'Marketing Employee',
      department: 'Marketing',
      team: 'Marketing',
      is_manager: false,
      reports: [],
    },
  },
  {
    id: 'sales_employee',
    label: 'Sales Employee',
    subtitle: 'Blue · Sales',
    tier_hint: 'blue',
    data: {
      employee_id: 'EMP-5500',
      name: 'Sales Employee',
      department: 'Sales',
      team: 'Sales',
      is_manager: false,
      reports: [],
    },
  },
  {
    id: 'devops_employee',
    label: 'DevOps Employee',
    subtitle: 'Blue · DevOps',
    tier_hint: 'blue',
    data: {
      employee_id: 'EMP-4010',
      name: 'DevOps Employee',
      department: 'DevOps',
      team: 'DevOps',
      is_manager: false,
      reports: [],
    },
  },
  {
    id: 'grey_legal_claimant',
    label: 'Grey Legal Claimant',
    subtitle: 'Grey · Legal (unverified)',
    tier_hint: 'grey',
    data: {
      employee_id: 'EMP-0099',
      name: 'Grey Legal Claimant',
      department: 'Legal',
      team: 'Legal',
      verified: false,
      is_manager: false,
      reports: [],
    },
  },
  {
    id: 'grey_finance_claimant',
    label: 'Grey Finance Claimant',
    subtitle: 'Grey · Finance (unverified)',
    tier_hint: 'grey',
    data: {
      employee_id: 'EMP-0099',
      name: 'Grey Finance Claimant',
      department: 'Finance',
      team: 'Finance',
      verified: false,
      is_manager: false,
      reports: [],
    },
  },
  {
    id: 'grey_engineering_claimant',
    label: 'Grey Engineering Claimant',
    subtitle: 'Grey · Engineering (unverified)',
    tier_hint: 'grey',
    data: {
      employee_id: 'EMP-0099',
      name: 'Grey Engineering Claimant',
      department: 'Engineering',
      team: 'Engineering',
      verified: false,
      is_manager: false,
      reports: [],
    },
  },
  {
    id: 'red_untrusted',
    label: 'Red Untrusted User',
    subtitle: 'Red · Unverified / high-risk',
    tier_hint: 'red',
    data: {
      employee_id: 'EMP-9999',
      name: 'Untrusted User',
      verified: false,
      is_manager: false,
      reports: [],
    },
  },
]

/** Look up a profile by id. Returns undefined if not found. */
export function findProfile(id) {
  return PROFILES.find(p => p.id === id)
}
