import type { Api } from 'grammy';
import type { InlineKeyboardMarkup } from 'grammy/types';
import { clearOutbound, isClearance, type SafetyClearance } from '@wlos/safety';
import { isInQuietHours, fa, type MessageKind } from '@wlos/shared';
import type { WlosRepos } from '@wlos/memory';

/**
 * THE single choke point for every message WLOS sends.
 *
 * Enforces, in order:
 *  1. a real SafetyClearance (type-branded — agents cannot forge it)
 *  2. crisis-mode suppression of ordinary coaching
 *  3. pause / snooze / stop-for-today
 *  4. quiet hours 00:00–07:00 Sydney (kind='safety' bypasses)
 *  5. the 20-message hard daily cap counted per Sydney local day
 *     (kind='safety' bypasses, and the bypass is recorded)
 *  6. sensitive content → neutral envelope + reveal button
 *     (lock-screen previews never contain sensitive words)
 *
 * There is deliberately NO other sendMessage call site in the codebase.
 */

export interface OutboxDeps {
  api: Api;
  repos: WlosRepos;
  now?: () => Date;
}

export interface SendRequest {
  userId: string;
  chatId: bigint;
  kind: MessageKind;
  sensitivity: 'low' | 'medium' | 'high';
  clearance: SafetyClearance;
  keyboard?: InlineKeyboardMarkup;
  /** direct replies to a user action skip cap-decline messaging but still count */
  isDirectReply?: boolean;
}

export type SendResult =
  | { sent: true; messageId: number; enveloped: boolean }
  | { sent: false; reason: string };

export async function sendViaOutbox(deps: OutboxDeps, req: SendRequest): Promise<SendResult> {
  const now = deps.now?.() ?? new Date();

  if (!isClearance(req.clearance)) {
    return { sent: false, reason: 'missing_safety_clearance' };
  }

  const user = await deps.repos.db.user.findUnique({
    where: { id: req.userId },
    include: { notificationPref: true },
  });
  if (!user || user.deletedAt) return { sent: false, reason: 'user_gone' };
  const prefs = user.notificationPref;

  const isSafety = req.kind === 'safety';

  // crisis mode: only safety + direct replies pass
  if (!isSafety && !req.isDirectReply && user.crisisModeUntil && now < user.crisisModeUntil) {
    return { sent: false, reason: 'crisis_mode' };
  }

  if (prefs && !isSafety && !req.isDirectReply) {
    if (prefs.paused) return { sent: false, reason: 'paused' };
    if (prefs.snoozedUntil && now < prefs.snoozedUntil) return { sent: false, reason: 'snoozed' };
    const quiet =
      !prefs.quietSuspended &&
      isInQuietHours(now, prefs.timezone, prefs.quietStart, prefs.quietEnd);
    if (quiet) return { sent: false, reason: 'quiet_hours' };
  }

  // hard cap — counts EVERY outbound message kind
  const cap = prefs?.dailyCap ?? 20;
  const sentToday = await deps.repos.countOutboundToday(req.userId, now);
  if (!isSafety && sentToday >= cap) {
    return { sent: false, reason: 'daily_cap' };
  }

  const text = req.clearance.text;
  const sensitive = req.sensitivity === 'high';

  let messageId: number;
  let preview: string;
  if (sensitive && !req.isDirectReply) {
    // neutral envelope; content revealed only on tap
    preview = fa.PRIVATE_ENVELOPE;
    const sentMsg = await deps.api.sendMessage(Number(req.chatId), fa.PRIVATE_ENVELOPE, {
      reply_markup: {
        inline_keyboard: [[{ text: fa.REVEAL_BUTTON, callback_data: 'reveal' }]],
      },
    });
    messageId = sentMsg.message_id;
    await deps.repos.db.auditLog.create({
      data: { userId: req.userId, actor: 'system', action: 'sensitive_enveloped', detail: null },
    });
    // stash the real content for the reveal callback
    await deps.repos.db.memory.upsert({
      where: {
        userId_layer_key: { userId: req.userId, layer: 'dynamic_state', key: `reveal:${messageId}` },
      },
      create: {
        userId: req.userId,
        layer: 'dynamic_state',
        key: `reveal:${messageId}`,
        content: JSON.stringify({ text, keyboard: req.keyboard ?? null }),
        sensitive: true,
        provenance: 'outbox_envelope',
        expiresAt: new Date(now.getTime() + 24 * 3600 * 1000),
      },
      update: { content: JSON.stringify({ text, keyboard: req.keyboard ?? null }) },
    });
  } else {
    preview = text.slice(0, 60);
    const sentMsg = await deps.api.sendMessage(Number(req.chatId), text, {
      reply_markup: req.keyboard,
    });
    messageId = sentMsg.message_id;
  }

  await deps.repos.recordOutbound(
    req.userId,
    req.kind,
    req.sensitivity,
    preview,
    isSafety && sentToday >= cap,
  );

  if (req.clearance.blocked || req.clearance.violations.length > 0) {
    await deps.repos.recordSafetyEvent(
      req.userId,
      'outbound',
      req.clearance.blocked ? 'urgent_medical' : 'caution',
      req.clearance.violations.map((v) => v.code),
      req.clearance.blocked ? 'message_blocked' : 'violation_logged',
    );
  }

  return { sent: true, messageId, enveloped: sensitive && !req.isDirectReply };
}

/** Convenience: clear + send a low-sensitivity direct reply. */
export async function replySafe(
  deps: OutboxDeps,
  userId: string,
  chatId: bigint,
  text: string,
  keyboard?: InlineKeyboardMarkup,
): Promise<SendResult> {
  return sendViaOutbox(deps, {
    userId,
    chatId,
    kind: 'reply',
    sensitivity: 'low',
    clearance: clearOutbound(text),
    keyboard,
    isDirectReply: true,
  });
}
