function compactText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

export function clean(value) {
  return compactText(value);
}

export function dedupe(values) {
  return [...new Set((values || []).map((value) => compactText(value)).filter(Boolean))];
}

function extractIdentifierValues(source, pattern) {
  return dedupe([...source.matchAll(pattern)].map((match) => match[1] || match[0]));
}

function classifyLink({ href, text }) {
  const source = `${href} ${text}`.toLowerCase();
  if (/(login|sign[ -]?in|logout|auth|nafath|otp|sso|keycloak)/.test(source)) return 'auth';
  if (/(download|export|pdf|csv|xlsx|attachment|document)/.test(source)) return 'download';
  if (/(process|eligibility|approval|submit|claim|preauth|authorization)/.test(source)) return 'process';
  if (/(api|graphql|fhir|rest)/.test(source)) return 'api';
  return 'navigation';
}

export function extractSetupHints(text) {
  const source = clean(text);

  const urls = dedupe(source.match(/https?:\/\/[^\s"'<>\)]+/gi) || []);
  const ipUrls = urls.filter((url) => /https?:\/\/\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?/i.test(url));
  const processUrls = urls.filter((url) => /process-message|eligibility|approval|submitclaim|claim|preauth|authorization/i.test(url));
  const relativePaths = dedupe(source.match(/\/(?:[A-Za-z0-9._-]+\/){0,6}[A-Za-z0-9._-]+/g) || []).slice(0, 50);

  return {
    urls,
    processUrls,
    ipUrls,
    relativePaths,
    ids: {
      chi: extractIdentifierValues(source, /(?:CHI\s*ID|CHIID)\s*[:=]?\s*(\d{3,10})/gi),
      nphies: extractIdentifierValues(source, /(?:NPHIES\s*ID|NPIES\s*ID|NPHIES\s*NUMBER)\s*[:=]?\s*(\d{6,20})/gi),
      provider: extractIdentifierValues(source, /(?:Provider\s*ID|Facility\s*ID)\s*[:=]?\s*(\d{3,12})/gi),
      claim: extractIdentifierValues(source, /(?:Claim\s*(?:ID|No\.?|Number)|Reference\s*(?:ID|No\.?))\s*[:=#-]?\s*([A-Z0-9-]{4,30})/gi),
      batch: extractIdentifierValues(source, /(?:Batch\s*(?:ID|No\.?|Number))\s*[:=#-]?\s*([A-Z0-9-]{4,30})/gi),
      invoice: extractIdentifierValues(source, /(?:Invoice\s*(?:ID|No\.?|Number))\s*[:=#-]?\s*([A-Z0-9-]{4,30})/gi)
    }
  };
}

export function normalizeLinks(links, currentUrl) {
  return (links || [])
    .map((link) => {
      const href = clean(link?.href);
      const text = clean(link?.text);
      if (!href && !text) return null;

      let absoluteUrl = '';
      if (href) {
        try {
          absoluteUrl = new URL(href, currentUrl).toString();
        } catch {
          absoluteUrl = href;
        }
      }

      return {
        text,
        href,
        absoluteUrl,
        kind: classifyLink({ href: absoluteUrl || href, text })
      };
    })
    .filter(Boolean)
    .slice(0, 100);
}

export function normalizeForms(forms) {
  return (forms || [])
    .map((form) => ({
      tag: clean(form?.tag),
      type: clean(form?.type),
      name: clean(form?.name),
      id: clean(form?.id),
      placeholder: clean(form?.placeholder),
      text: clean(form?.text)
    }))
    .filter((form) => Object.values(form).some(Boolean))
    .slice(0, 100);
}

export function normalizeTables(tables) {
  return (tables || [])
    .map((table, index) => ({
      index,
      headers: Array.isArray(table?.headers) ? table.headers.map(clean).filter(Boolean).slice(0, 20) : [],
      rows: Array.isArray(table?.rows)
        ? table.rows
            .map((row) => (Array.isArray(row) ? row.map(clean).filter(Boolean).slice(0, 20) : []))
            .filter((row) => row.length > 0)
            .slice(0, 10)
        : [],
      rowCount: Number.isFinite(table?.rowCount) ? table.rowCount : Array.isArray(table?.rows) ? table.rows.length : 0
    }))
    .filter((table) => table.headers.length > 0 || table.rows.length > 0)
    .slice(0, 10);
}

export function buildNormalizedExtraction({
  source,
  portalUrl,
  currentUrl,
  title,
  capturedAt,
  auth,
  bodyText,
  html,
  links,
  formHints,
  tables,
  notes
}) {
  const normalizedLinks = normalizeLinks(links, currentUrl || portalUrl);
  const normalizedForms = normalizeForms(formHints);
  const normalizedTables = normalizeTables(tables);
  const setupHints = extractSetupHints(`${clean(bodyText)}\n${clean(html)}`);

  return {
    source: clean(source),
    portalUrl: clean(portalUrl),
    currentUrl: clean(currentUrl || portalUrl),
    title: clean(title),
    capturedAt: clean(capturedAt),
    auth: {
      attempted: Boolean(auth?.attempted),
      mode: clean(auth?.mode),
      likelySuccessful: Boolean(auth?.likelySuccessful)
    },
    endpoints: setupHints,
    links: normalizedLinks,
    forms: normalizedForms,
    tables: normalizedTables,
    notes: dedupe(notes || [])
  };
}