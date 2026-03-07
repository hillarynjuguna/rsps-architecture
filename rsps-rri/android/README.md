# Android Build Instructions

This directory contains the RSPS-RRI Android application.  The project is a
standard Android Studio/Gradle project targeting **minSdk 26** and
**targetSdk 34**.

## Prerequisites

- Android SDK (command-line tools) installed on your machine
- Java 17 or later
- (Optional) Android Studio Arctic Fox or newer

The `gradle` commandline tool is available in this devcontainer but build
environment may lack the Android SDK and required repositories.  It is
recommended to open the project in Android Studio and let it configure the
SDK for you.

## Generating a Wrapper

To avoid relying on a system-wide Gradle, you can generate a wrapper:

```bash
cd android
# this will download plugins, ensure you have network access
gradle wrapper
```

After the wrapper is present you can run `./gradlew` instead of `gradle`.

## Building

Assuming the SDK is installed and `ANDROID_HOME`/`ANDROID_SDK_ROOT` are set:

```bash
cd android
./gradlew assembleDebug
```

The resulting APK will be in `app/build/outputs/apk/debug/app-debug.apk`.

You can install it on a connected device (e.g. Samsung S21) with:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

or use `adb` to push it to a device/emulator of your choice.

## Running on Device

1. Enable **Developer options** and **USB debugging** on your phone.
2. Connect it via USB or use `adb connect <device-ip>` over Wi‑Fi.
3. Execute the `adb install` command above.

## Notes

- This project currently does not include any Play Services or special
  signing keys; the debug build uses the default debug key.
- For production deployment you will need to create a release key and
  configure `signingConfigs` in `android/app/build.gradle`.
