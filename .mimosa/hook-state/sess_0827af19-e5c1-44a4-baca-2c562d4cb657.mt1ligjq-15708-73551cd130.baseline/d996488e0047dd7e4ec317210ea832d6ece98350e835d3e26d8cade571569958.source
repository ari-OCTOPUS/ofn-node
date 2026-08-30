import type { ConsentScope } from '@wlos/shared';

/**
 * Task-specific context packet builder — the consent/minimization firewall
 * between WLOS memory and any LLM. The LLM never sees raw history.
 *
 * Rules enforced here (spec §8 / non-negotiables 13–14):
 *  - only task-relevant sections are included
 *  - sensitive categories (cannabis, psychology) require BOTH consent AND
 *    a task that genuinely needs them (`needs` allowlist)
 *  - a redactor strips identifiers as the final step
 *  - what was included (categories, not content) is returned for llm_calls audit
 */

export type DataCategory =
  | 'profile_minimal'
  | 'weights'
  | 'meals'
  | 'workouts'
  | 'sleep'
  | 'subjective_state'
  | 'patterns'
  | 'experiments'
  | 'psychology'
  | 'cannabis'
  | 'coach_notes';

const SENSITIVE: Record<'psychology' | 'cannabis', ConsentScope> = {
  psychology: 'psychology',
  cannabis: 'cannabis',
};

export interface PacketSection {
  category: DataCategory;
  content: string;
}

export interface BuildPacketInput {
  purpose: string;
  sections: PacketSection[];
  /** categories this task is allowed to use at all */
  needs: DataCategory[];
  /** current consent state */
  consents: Partial<Record<ConsentScope, boolean>>;
  redactor: (text: string) => string;
  maxChars?: number;
}

export interface BuiltPacket {
  purpose: string;
  dataCategories: DataCategory[];
  content: string;
  excluded: Array<{ category: DataCategory; reason: 'not_needed' | 'no_consent' | 'over_budget' }>;
}

export function buildContextPacket(input: BuildPacketInput): BuiltPacket {
  const included: PacketSection[] = [];
  const excluded: BuiltPacket['excluded'] = [];
  const maxChars = input.maxChars ?? 6000;
  let used = 0;

  for (const section of input.sections) {
    if (!input.needs.includes(section.category)) {
      excluded.push({ category: section.category, reason: 'not_needed' });
      continue;
    }
    const scope = (SENSITIVE as Partial<Record<DataCategory, ConsentScope>>)[section.category];
    if (scope && input.consents[scope] !== true) {
      excluded.push({ category: section.category, reason: 'no_consent' });
      continue;
    }
    if (used + section.content.length > maxChars) {
      excluded.push({ category: section.category, reason: 'over_budget' });
      continue;
    }
    used += section.content.length;
    included.push(section);
  }

  const body = included.map((s) => `## ${s.category}\n${s.content}`).join('\n\n');
  return {
    purpose: input.purpose,
    dataCategories: included.map((s) => s.category),
    content: input.redactor(body),
    excluded,
  };
}
