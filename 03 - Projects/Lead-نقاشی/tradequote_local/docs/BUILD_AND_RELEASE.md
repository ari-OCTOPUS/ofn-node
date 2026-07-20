# Build & Release Guide

From this repository to an APK installed on the Samsung Galaxy S23 FE.
Written for a Windows PC; macOS/Linux commands are identical unless noted.

## 0. One-time machine setup (~30–60 min)

1. Install **Flutter (stable)**: https://docs.flutter.dev/get-started/install
   — at authoring time stable was **3.44.0**.
2. Install **Android Studio** (brings the Android SDK):
   https://developer.android.com/studio
3. In a terminal:

   ```bash
   flutter doctor
   flutter doctor --android-licenses    # accept all
   ```

   Fix anything `flutter doctor` marks red for Android.

## 1. First build

From the repository root (`tradequote_local/`):

```bash
# 1) Generate the android/ platform folder matched to YOUR Flutter version.
#    This does NOT touch lib/ or pubspec.yaml.
flutter create . --org au.com.placeholder --project-name tradequote_local --platforms android

# 2) Fetch dependencies
flutter pub get

# 3) Generate drift database code (creates lib/data/db/database.g.dart)
dart run build_runner build --delete-conflicting-outputs

# 4) Static analysis
flutter analyze

# 5) Tests
flutter test
```

### Expected first-run notes (honest)

- This code was written in a workspace that could not compile Dart
  (PROJECT_STATE.md). `flutter analyze` may report a handful of small
  issues (a renamed parameter, a missing import). They are normally
  one-line fixes; fix them or paste the output back into a Claude session
  with this repo and ask it to fix them.
- If `flutter pub get` fails on **flutter_email_sender ^9.0.0** (released
  the same day as research), change it to `^8.0.0` in pubspec.yaml and
  rerun — the API used is identical.
- If `flutter test` fails ONLY in `repository_test.dart` with a message
  about loading sqlite3 on Windows, see docs/testing/TEST_PLAN.md
  §Environment (you need sqlite3.dll on PATH, or run tests on
  macOS/Linux/WSL). The GST/ABN/money tests run anywhere.

### Set the app name (recommended)

`flutter create` sets the launcher label to `tradequote_local`. Open
`android/app/src/main/AndroidManifest.xml` and change:

```xml
android:label="TradeQuote Local"
```

Commit `pubspec.lock` after the first successful `flutter pub get`.

## 2. Run on the S23 FE (smoke test)

1. On the phone: Settings → About phone → Software information → tap
   **Build number** 7× → back → **Developer options** → enable
   **USB debugging**.
2. Connect USB, allow the prompt, then:

   ```bash
   flutter devices        # should list the SM-S711…
   flutter run --release
   ```

3. Walk through `docs/testing/MANUAL_ACCEPTANCE_CHECKLIST.md`.

## 3. Build the APK

```bash
flutter build apk --release
```

Output: `build/app/outputs/flutter-apk/app-release.apk`

The default Flutter template signs release builds with the **debug key** —
fine for installing on your own phone, NOT for Play Store distribution.

Checksum (PowerShell): `Get-FileHash .\app-release.apk -Algorithm SHA256`
(macOS/Linux: `shasum -a 256 app-release.apk`).

### Install on the phone without USB

Copy the APK to the phone (or share it to yourself), open it from
**My Files**, and allow "Install unknown apps" for My Files when asked.

## 4. Proper release signing (before any wider distribution)

```bash
keytool -genkey -v -keystore %USERPROFILE%\tradequote-release.jks ^
  -keyalg RSA -keysize 2048 -validity 10000 -alias tradequote
```

Create `android/key.properties` (NEVER commit it — it is gitignored):

```properties
storePassword=…
keyPassword=…
keyAlias=tradequote
storeFile=C:/Users/you/tradequote-release.jks
```

Then follow the standard Flutter signing wiring in
https://docs.flutter.dev/deployment/android#sign-the-app (add the
`signingConfigs` block to `android/app/build.gradle.kts`). Keep the
keystore backed up — losing it means losing update continuity.

## 5. Renaming before public distribution

The placeholder application ID is `au.com.placeholder.tradequote_local`.
To rename: change `applicationId` in `android/app/build.gradle.kts`, the
label in AndroidManifest.xml, and `kAppName` in `lib/providers.dart`.
Branding is centralised in `kAppName` — screens read it from there.

## 6. Version stamping

Bump `version:` in pubspec.yaml (e.g. `0.2.0+2`) for each release, note
changes in CHANGELOG.md, and rebuild.

## 7. Later: Windows desktop

`flutter create . --platforms windows` then `flutter build windows`. All
chosen packages support Windows except flutter_email_sender (the share
service falls back to the share sheet / manual flow); test before relying
on it. This is a phase-2 target (FUTURE_EXTENSIONS.md).
