import { fa, normalizeDigits, normalizeFa } from '@wlos/shared';
import { parseWeight } from '@wlos/nutrition-engine';
import type { WlosRepos } from '@wlos/memory';

/**
 * Onboarding FSM — Persian, one question at a time, resumable.
 * Cursor lives in UserProfile.onboardingStep.
 */

type Step = 'welcome' | 'name' | 'sex' | 'age' | 'height' | 'weight' | 'goal' | 'consent' | 'done';

const ORDER: Step[] = ['welcome', 'name', 'sex', 'age', 'height', 'weight', 'goal', 'consent', 'done'];

export interface OnboardingReply {
  text: string;
  keyboard?: Array<Array<{ text: string; callback_data: string }>>;
  finished: boolean;
}

export async function startOnboarding(repos: WlosRepos, userId: string): Promise<OnboardingReply> {
  await setStep(repos, userId, 'name');
  return {
    text: `${fa.WELCOME}\n\n${fa.DISCLAIMER}\n\n${fa.ASK_NAME}`,
    finished: false,
  };
}

export async function handleOnboardingInput(
  repos: WlosRepos,
  userId: string,
  raw: string,
): Promise<OnboardingReply | null> {
  const profile = await repos.db.userProfile.findUnique({ where: { userId } });
  if (!profile) return null;
  const step = profile.onboardingStep as Step;
  if (step === 'done' || step === 'welcome') return null;

  const text = normalizeFa(normalizeDigits(raw)).trim();

  switch (step) {
    case 'name': {
      if (text.length < 1 || text.length > 60) return ask('name');
      await repos.db.user.update({ where: { id: userId }, data: { displayName: text } });
      await setStep(repos, userId, 'sex');
      return {
        text: `خوشبختم ${text}! 🙌\n${fa.ASK_SEX}`,
        keyboard: [
          [
            { text: 'مرد', callback_data: 'ob:sex:male' },
            { text: 'زن', callback_data: 'ob:sex:female' },
          ],
        ],
        finished: false,
      };
    }
    case 'age': {
      const age = Number(text);
      if (!Number.isInteger(age) || age < 16 || age > 90) return ask('age');
      const year = new Date().getFullYear() - age;
      await repos.db.userProfile.update({ where: { userId }, data: { birthYear: year } });
      await setStep(repos, userId, 'height');
      return { text: fa.ASK_HEIGHT, finished: false };
    }
    case 'height': {
      const h = Number(text.replace(/[^\d.]/g, ''));
      if (!h || h < 120 || h > 230) return ask('height');
      await repos.db.userProfile.update({ where: { userId }, data: { heightCm: h } });
      await setStep(repos, userId, 'weight');
      return { text: fa.ASK_WEIGHT, finished: false };
    }
    case 'weight': {
      const w = parseWeight(text);
      if (!w) return ask('weight');
      await repos.logWeight(userId, w);
      await setStep(repos, userId, 'goal');
      return { text: fa.ASK_GOAL, finished: false };
    }
    case 'goal': {
      if (text.length < 2) return ask('goal');
      const goalW = parseWeight(text); // optional numeric goal inside the text
      await repos.db.userProfile.update({
        where: { userId },
        data: { goalNote: text, goalWeightKg: goalW ?? undefined },
      });
      await setStep(repos, userId, 'consent');
      return consentStep();
    }
    default:
      return null;
  }
}

export async function handleOnboardingCallback(
  repos: WlosRepos,
  userId: string,
  data: string,
): Promise<OnboardingReply | null> {
  if (data === 'ob:sex:male' || data === 'ob:sex:female') {
    await repos.db.userProfile.update({
      where: { userId },
      data: { sex: data === 'ob:sex:male' ? 'male' : 'female' },
    });
    await setStep(repos, userId, 'age');
    return { text: fa.ASK_AGE, finished: false };
  }
  if (data.startsWith('ob:consent:')) {
    const [, , scope, val] = data.split(':');
    if (scope === 'finish') {
      await setStep(repos, userId, 'done');
      return { text: fa.ONBOARD_DONE, finished: true };
    }
    if (scope && (val === 'on' || val === 'off')) {
      await repos.setConsent(userId, scope as never, val === 'on');
      const label = scope === 'psychology' ? fa.CONSENT_PSY : scope === 'cannabis' ? fa.CONSENT_CANNABIS : fa.CONSENT_COACH;
      return {
        text: `${label}: ${val === 'on' ? fa.CONSENT_ON : fa.CONSENT_OFF}`,
        keyboard: consentKeyboard(),
        finished: false,
      };
    }
  }
  return null;
}

function consentStep(): OnboardingReply {
  return {
    text: [
      fa.CONSENT_INTRO,
      '',
      `1️⃣ ${fa.CONSENT_PSY}`,
      `2️⃣ ${fa.CONSENT_CANNABIS}`,
      `3️⃣ ${fa.CONSENT_COACH}`,
      '',
      'هر کدوم رو که می‌خوای روشن کن، بعد «تمام» رو بزن:',
    ].join('\n'),
    keyboard: consentKeyboard(),
    finished: false,
  };
}

function consentKeyboard() {
  return [
    [
      { text: '🧠 روان‌شناسی: روشن', callback_data: 'ob:consent:psychology:on' },
      { text: 'خاموش', callback_data: 'ob:consent:psychology:off' },
    ],
    [
      { text: '🌿 cannabis: روشن', callback_data: 'ob:consent:cannabis:on' },
      { text: 'خاموش', callback_data: 'ob:consent:cannabis:off' },
    ],
    [
      { text: '👥 اشتراک با مربی: روشن', callback_data: 'ob:consent:coach_sharing:on' },
      { text: 'خاموش', callback_data: 'ob:consent:coach_sharing:off' },
    ],
    [{ text: '✅ تمام', callback_data: 'ob:consent:finish' }],
  ];
}

function ask(step: Step): OnboardingReply {
  const map: Record<Step, string> = {
    welcome: fa.WELCOME,
    name: fa.ASK_NAME,
    sex: fa.ASK_SEX,
    age: 'یک عدد بین ۱۶ تا ۹۰ بفرست:',
    height: 'قد به سانتی‌متر، مثلاً 178:',
    weight: 'وزن به کیلوگرم، مثلاً ۹۴٫۵:',
    goal: fa.ASK_GOAL,
    consent: fa.CONSENT_INTRO,
    done: fa.ONBOARD_DONE,
  };
  return { text: map[step], finished: false };
}

async function setStep(repos: WlosRepos, userId: string, step: Step): Promise<void> {
  await repos.db.userProfile.update({ where: { userId }, data: { onboardingStep: step } });
}

export function isOnboarding(step: string): boolean {
  return ORDER.includes(step as Step) && step !== 'done';
}
