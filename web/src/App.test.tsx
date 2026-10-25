import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { App } from './App'
import { SeverityBadge } from './components/SeverityBadge'
import { RiskDial } from './components/RiskDial'
import { Redline } from './components/Redline'

// Mock the API client while preserving ApiError class
vi.mock('./lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./lib/api')>()
  return {
    ...actual,
    fetchHealth: vi.fn().mockResolvedValue({
      status: 'ok',
      app: 'moroccan-law-ai',
      corpus_articles_count: 50,
      bo_issues_count: 18,
      total_consultations: 120,
      total_audits: 45,
    }),
    listBoIssues: vi.fn().mockResolvedValue({
      count: 2,
      issues: [
        {
          id: 'bo-7398',
          bo_issue: 'BO n° 7398',
          publication_date: '2025-04-10',
          law_number: 'Loi n° 43-22',
          title_fr: 'Dispositifs médicaux',
          title_ar: 'المستلزمات الطبية',
          domain: 'Santé',
          target_audience: ['Citizens', 'Tech Startups'],
          severity: 'MEDIUM',
          summary_fr: 'Réglementation des dispositifs médicaux.',
          summary_ar: 'تنظيم المستلزمات الطبية.',
          summary_darija: 'قوانين جديدة للمستلزمات الطبية.',
          amendments: [],
        },
      ],
    }),
    askLegalQuery: vi.fn().mockResolvedValue({
      query: 'délai de préavis',
      domain: 'labor_law',
      citation_verified: true,
      verbatim_citations: [
        {
          id: 'travail-art-43',
          code: 'Code du Travail',
          law_number: 'Loi n° 65-99',
          dahir: 'Dahir n° 1-03-194',
          bo_issue: 'BO n° 5167',
          publication_date: '2003-12-08',
          article: 'Article 43',
          text_fr: 'Le délai de préavis court...',
          text_ar: 'يبدأ أجل الإخطار...',
        },
      ],
      simplified_explanation: {
        fr: 'Explication en français.',
        ar: 'شرح بالعربية.',
        darija: 'شرح بالدارجة.',
      },
      legal_disclaimer: 'Avertissement officiel.',
    }),
    computeCustomDiff: vi.fn().mockResolvedValue({
      article_ref: 'Article 10',
      bo_issue: 'BO n° 7000',
      old_text: 'Texte ancien',
      new_text: 'Texte nouveau modifié',
      added_tokens: ['nouveau', 'modifié'],
      removed_tokens: ['ancien'],
      change_ratio: 0.5,
      similarity_ratio: 0.5,
      compliance_severity: 'MEDIUM',
      redline_html: 'Texte <del>ancien</del> <ins>nouveau modifié</ins>',
    }),
    auditContract: vi.fn().mockResolvedValue({
      status: 'NON_COMPLIANT_HIGH_RISK',
      risk_score: 85,
      violations_count: 2,
      violations: [
        {
          id: 'probation_excess',
          category: 'Durée d’essai excessive',
          severity: 'HIGH',
          explanation: 'Période supérieure au maximum du Code du Travail',
          statutory_basis: 'Article 14 du Code du Travail',
          remediation_fr: 'Réduire à 3 mois maximum.',
          remediation_ar: 'تقليص المدة إلى 3 أشهر.',
        },
      ],
      disclaimer: 'Avertissement juridique.',
    }),
  }
})

describe('Mizan App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the header and navigation links', async () => {
    render(<App />)

    // Check brand title
    expect(screen.getAllByText('Mizan').length).toBeGreaterThan(0)

    // Check primary navigation links exist (in desktop and mobile navigation)
    expect(screen.getAllByRole('link', { name: /consultation/i }).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByRole('link', { name: /bulletin officiel/i }).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByRole('link', { name: /comparateur/i }).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByRole('link', { name: /contrôle de contrat/i }).length).toBeGreaterThanOrEqual(1)
  })

  it('switches between views via navigation links', async () => {
    render(<App />)

    // Verify link hrefs
    const boLinks = screen.getAllByRole('link', { name: /bulletin officiel/i })
    expect(boLinks[0]).toHaveAttribute('href', '#/gazette')

    const compareLinks = screen.getAllByRole('link', { name: /comparateur/i })
    expect(compareLinks[0]).toHaveAttribute('href', '#/compare')

    const auditLinks = screen.getAllByRole('link', { name: /contrôle de contrat/i })
    expect(auditLinks[0]).toHaveAttribute('href', '#/audit')

    // Simulate route hashchange to gazette
    window.location.hash = '#/gazette'
    window.dispatchEvent(new HashChangeEvent('hashchange'))

    await waitFor(() => {
      expect(boLinks[0]).toHaveAttribute('aria-current', 'page')
    })
  })

  it('switches language to Arabic and changes direction to rtl', async () => {
    render(<App />)

    // Find and click the Arabic radio button (label: "عربي")
    const arRadio = screen.getByRole('radio', { name: 'عربي' })
    fireEvent.click(arRadio)

    // The document or app wrapper should reflect Arabic text
    await waitFor(() => {
      expect(document.documentElement.getAttribute('dir')).toBe('rtl')
      expect(document.documentElement.getAttribute('lang')).toBe('ar')
    })

    // Switch back to French
    const frRadio = screen.getByRole('radio', { name: 'FR' })
    fireEvent.click(frRadio)

    await waitFor(() => {
      expect(document.documentElement.getAttribute('dir')).toBe('ltr')
      expect(document.documentElement.getAttribute('lang')).toBe('fr')
    })
  })
})

describe('SeverityBadge Component', () => {
  it('renders critical badge with appropriate styling', () => {
    const { container } = render(<SeverityBadge severity="CRITICAL" />)
    expect(screen.getByText(/Critique/i)).toBeInTheDocument()
    expect(container.firstChild).toHaveClass('text-sev-crit')
  })

  it('renders low badge with appropriate styling', () => {
    const { container } = render(<SeverityBadge severity="LOW" />)
    expect(screen.getByText(/Faible/i)).toBeInTheDocument()
    expect(container.firstChild).toHaveClass('text-ink-3')
  })
})

describe('RiskDial Component', () => {
  it('renders with score and label', () => {
    render(<RiskDial score={75} status="REVIEW_REQUIRED" />)
    expect(screen.getByText('75')).toBeInTheDocument()
    expect(screen.getByText(/\/ 100/)).toBeInTheDocument()
  })
})

describe('Redline Component', () => {
  it('renders parsed redline markdown with del and ins', () => {
    const rawMarkdown = 'Texte initial [-supprimé-] {+ajouté+} final'
    render(<Redline markdown={rawMarkdown} />)
    expect(screen.getByText('supprimé')).toBeInTheDocument()
    expect(screen.getByText('ajouté')).toBeInTheDocument()
  })
})
