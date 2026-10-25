export type UiLang = 'fr' | 'ar' | 'en'
export type AnswerLang = 'fr' | 'ar' | 'darija'
export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export interface Health {
  status: string
  app: string
  retrieval_engine: string
  corpus_articles_count: number
  bo_issues_count: number
  consultations_logged: number
  contract_audits_logged: number
}

export interface Citation {
  id: string
  code: string
  law_number: string
  dahir: string
  bo_issue: string
  publication_date: string
  article: string
  topic: string
  text_ar: string
  text_fr: string
  rrf_score?: number
}

export interface QueryTranslation {
  original_query: string
  detected_darija: boolean
  domain: string
  expanded_terms: string[]
  augmented_query: string
}

export interface QueryResult {
  query: string
  domain: string
  retrieval_engine: string
  query_translation: QueryTranslation
  verbatim_citations: Citation[]
  ai_commentary: { ar: string; fr: string; darija: string }
  citation_verified: boolean
  legal_disclaimer: string
}

export interface RedlineDiff {
  article_ref: string
  bo_issue: string
  old_text: string
  new_text: string
  added_tokens: string[]
  removed_tokens: string[]
  change_ratio: number
  similarity_ratio: number
  compliance_severity: Severity
  redline_markdown: string
}

export type Provenance = 'curated_paraphrase' | 'gazette_index_summary'

export interface Amendment {
  code: string
  article_ref: string
  provenance: Provenance
  old_text: string | null
  new_text: string | null
  summary_ar: string
  summary_fr: string
  summary_darija: string
  redline_diff: RedlineDiff | null
}

export interface BoIssue {
  bo_number: string
  edition: string
  publication_date: string
  title_ar: string
  title_fr: string
  source_url: string
  total_pages?: number
  target_audiences: string[]
  amendments: Amendment[]
}

export type AuditStatus = 'COMPLIANT' | 'REVIEW_REQUIRED' | 'NON_COMPLIANT_HIGH_RISK'

export interface Violation {
  rule_id: string
  title: string
  statutory_reference: string
  severity: Severity
  remediation: string
}

export interface AuditResult {
  status: AuditStatus
  risk_score: number
  violations_count: number
  rules_checked: number
  violations: Violation[]
  disclaimer: string
}
