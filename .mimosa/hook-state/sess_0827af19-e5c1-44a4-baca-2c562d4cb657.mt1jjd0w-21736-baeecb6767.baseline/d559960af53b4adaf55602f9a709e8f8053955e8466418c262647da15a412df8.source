// Minimal provider contract for future API adapters.
// A real adapter can implement collect(query) and return canonical RawItem objects.

export class SourceCollector {
  constructor({ name, version = '0.1.0' } = {}) {
    if (!name) throw new Error('SourceCollector requires a name');
    this.name = name;
    this.version = version;
  }

  async collect(_query) {
    throw new Error('collect(query) must be implemented by adapter');
  }

  capabilities() {
    return {
      name: this.name,
      version: this.version,
      methods: ['collect'],
      output_contract: 'raw-items.v1',
    };
  }
}

export class FixtureCollector extends SourceCollector {
  constructor(items = []) {
    super({ name: 'fixture-collector', version: '0.1.0' });
    this.items = items;
  }

  async collect(query = {}) {
    const q = String(query.query || '').toLowerCase();
    const limit = Math.min(Math.max(Number(query.limit || 10), 1), 50);
    return this.items
      .filter((item) => !q || JSON.stringify(item).toLowerCase().includes(q))
      .slice(0, limit);
  }
}
