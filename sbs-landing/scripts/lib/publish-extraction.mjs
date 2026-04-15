function clean(value) {
  return String(value || '').trim();
}

function collectTargets() {
  const mohBase = clean(process.env.MOH_BRIDGE_URL || process.env.NPHIES_BRIDGE_URL || '');
  const sinkUrl = clean(process.env.PORTAL_EXTRACTION_SINK_URL || '');
  const n8nWebhook = clean(process.env.N8N_PORTAL_EXTRACTION_WEBHOOK_URL || '');

  const targets = [];
  if (sinkUrl) {
    targets.push({ name: 'custom-sink', url: sinkUrl, payloadMode: 'record' });
  } else if (mohBase) {
    targets.push({
      name: 'moh-bridge',
      url: `${mohBase.replace(/\/+$/, '')}/portal-extractions`,
      payloadMode: 'record'
    });
  }

  if (n8nWebhook) {
    targets.push({ name: 'n8n-webhook', url: n8nWebhook, payloadMode: 'event' });
  }

  return targets;
}

function buildEventPayload(record) {
  return {
    eventType: 'portal.extraction.captured',
    capturedAt: record.capturedAt,
    source: record.source,
    extraction: record
  };
}

export async function publishNormalizedExtraction(record) {
  const targets = collectTargets();
  if (targets.length === 0) {
    return {
      published: false,
      targets: [],
      results: [],
      notes: ['No MOH/n8n sink configured. Set MOH_BRIDGE_URL or PORTAL_EXTRACTION_SINK_URL and optionally N8N_PORTAL_EXTRACTION_WEBHOOK_URL.']
    };
  }

  const results = [];
  for (const target of targets) {
    const payload = target.payloadMode === 'event' ? buildEventPayload(record) : record;
    try {
      const response = await fetch(target.url, {
        method: 'POST',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const responseText = await response.text();
      results.push({
        target: target.name,
        url: target.url,
        ok: response.ok,
        status: response.status,
        responsePreview: clean(responseText).slice(0, 300)
      });
    } catch (error) {
      results.push({
        target: target.name,
        url: target.url,
        ok: false,
        status: 0,
        responsePreview: clean(error?.message || 'publish failed')
      });
    }
  }

  return {
    published: results.some((item) => item.ok),
    targets: targets.map((target) => target.name),
    results,
    notes: []
  };
}
