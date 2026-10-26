import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AskView } from './AskView'
import { AuditView } from './AuditView'
import { CompareView } from './CompareView'
import { GazetteView } from './GazetteView'
import { I18nContext, DICTIONARIES } from '../lib/i18n'
import type { BoIssue, QueryResult } from '../lib/types'

vi.mock('../lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/api')>()
  return {
    ...actual,
    api: {
      ...actual.api,
      query: vi.fn().mockResolvedValue({
        query: 'délai de préavis',
        domain: 'labor_law',
        retrieval_engine: 'Hybrid Okapi BM25',
        citation_verified: true,
        query_translation: {
          original_query: 'délai de préavis',
          detected_darija: false,
          domain: 'labor_law',
          expanded_terms: ['préavis', 'licenciement'],
          augmented_query: 'délai de préavis préavis licenciement',
        },
        verbatim_citations: [
          {
            id: 'cit-1',
            code: 'Code du Travail',
            law_number: 'Loi n° 65-99',
            dahir: 'Dahir n° 1-03-194',
            bo_issue: 'BO n° 5167',
            publication_date: '2003-12-08',
            article: 'Article 43',
            topic: 'labor_law',
            text_fr: 'Le délai de préavis court à compter du lendemain...',
            text_ar: 'يبدأ أجل الإخطار من اليوم الموالي...',
            rrf_score: 0.0333,
          },
        ],
        ai_commentary: {
          fr: 'Le préavis est obligatoire sauf en cas de faute grave.',
          ar: 'أجل الإخطار إلزامي إلا في حالة الخطأ الجسيم.',
          darija: 'الإشعار واجب قبل ما يخرج الأجير.',
        },
        legal_disclaimer: 'Avertissement officiel.',
      } as QueryResult),
      auditContract: vi.fn().mockResolvedValue({
        status: 'NON_COMPLIANT_HIGH_RISK',
        risk_score: 85,
        violations_count: 1,
        violations: [
          {
            rule_id: 'v1',
            title: 'Durée d’essai excessive',
            severity: 'HIGH',
            statutory_reference: 'Article 14 du Code du Travail',
            remediation: 'Réduire à 3 mois maximum.',
          },
        ],
        disclaimer: 'Avertissement juridique.',
      }),
      diff: vi.fn().mockResolvedValue({
        article_ref: 'Loi 5-96, article 71',
        bo_issue: 'BO n° 6992',
        old_text: 'Texte ancien',
        new_text: 'Texte nouveau',
        redline_markdown: 'Texte [-ancien-] {+nouveau+}',
        added_tokens: ['nouveau'],
        removed_tokens: ['ancien'],
        change_ratio: 0.35,
        similarity_ratio: 0.65,
        compliance_severity: 'MEDIUM',
      }),
      boIssues: vi.fn().mockResolvedValue([
        {
          bo_number: 'BO n° 7398',
          edition: 'Générale',
          publication_date: '2025-04-10',
          title_fr: 'Dispositifs médicaux et produits de santé',
          title_ar: 'المستلزمات الطبية والمنتجات الصحية',
          source_url: 'http://www.sgg.gov.ma/bo/7398',
          total_pages: 42,
          target_audiences: ['Citizens', 'Tech Startups'],
          amendments: [
            {
              code: 'Loi 43-22',
              article_ref: 'Article 12',
              provenance: 'curated_paraphrase',
              old_text: 'Ancien texte',
              new_text: 'Nouveau texte',
              summary_fr: 'Agrément obligatoire pour les dispositifs médicaux.',
              summary_ar: 'ترخيص إجباري للمستلزمات الطبية.',
              summary_darija: 'لازم الترخيص للمستلزمات الطبية.',
              redline_diff: null,
            },
          ],
        } as BoIssue,
      ]),
    },
  }
})

function renderWithI18n(ui: React.ReactElement, lang: 'fr' | 'ar' | 'en' = 'fr') {
  return render(
    <I18nContext.Provider value={{ lang, s: DICTIONARIES[lang], setLang: vi.fn() }}>
      {ui}
    </I18nContext.Provider>,
  )
}

describe('Views Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('AskView', () => {
    it('renders header, allows typing and submits legal search', async () => {
      renderWithI18n(<AskView />)
      expect(screen.getByText('Poser une question de droit marocain')).toBeInTheDocument()

      const textarea = screen.getByPlaceholderText(/Par exemple/i)
      fireEvent.change(textarea, { target: { value: 'licenciement abusif' } })

      const submitBtn = screen.getByRole('button', { name: /Rechercher dans le corpus/i })
      fireEvent.click(submitBtn)

      await waitFor(() => {
        expect(screen.getByText('Code du Travail')).toBeInTheDocument()
        expect(screen.getByText('Article 43')).toBeInTheDocument()
      })
    })
  })

  describe('AuditView', () => {
    it('renders contract auditor, loads example and runs audit', async () => {
      renderWithI18n(<AuditView />)
      expect(screen.getByText('Contrôle de contrat')).toBeInTheDocument()

      // Clicking example button automatically populates and audits the contract
      const exampleBtn = screen.getByRole('button', { name: /Charger un exemple/i })
      fireEvent.click(exampleBtn)

      await waitFor(() => {
        expect(screen.getByText('Article 14 du Code du Travail')).toBeInTheDocument()
        expect(screen.getByText(/Durée d’essai excessive/i)).toBeInTheDocument()
      })
    })
  })

  describe('CompareView', () => {
    it('renders legislative redline comparator, loads example and executes diff', async () => {
      renderWithI18n(<CompareView />)
      expect(screen.getByText('Comparateur de textes')).toBeInTheDocument()

      // Clicking example button automatically populates and runs comparison
      const exampleBtn = screen.getByRole('button', { name: /Charger un exemple/i })
      fireEvent.click(exampleBtn)

      await waitFor(() => {
        expect(screen.getByText('35%')).toBeInTheDocument()
      })
    })
  })

  describe('GazetteView', () => {
    it('renders official gazette list and filters by keyword', async () => {
      renderWithI18n(<GazetteView />)
      expect(screen.getByText('Bulletin Officiel')).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getAllByText(/Dispositifs médicaux/i).length).toBeGreaterThan(0)
      })

      const searchInput = screen.getByPlaceholderText(/Rechercher un numéro/i)
      fireEvent.change(searchInput, { target: { value: 'médicaux' } })

      expect(screen.getAllByText(/Dispositifs médicaux/i).length).toBeGreaterThan(0)
    })
  })
})
