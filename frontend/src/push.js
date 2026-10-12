// Web Push with OneSignal. The SDK is loaded by a <script> tag in index.html.
const APP_ID = import.meta.env.VITE_ONESIGNAL_APP_ID;
const CONFIGURED = Boolean(APP_ID) && APP_ID !== "your_app_id";

window.OneSignalDeferred = window.OneSignalDeferred || [];

// Run code once the OneSignal SDK is ready
function withOneSignal(callback) {
  return new Promise((resolve, reject) => {
    window.OneSignalDeferred.push(async (OneSignal) => {
      try {
        resolve(await callback(OneSignal));
      } catch (error) {
        reject(error);
      }
    });
  });
}

// Remember whether OneSignal started, so the button can show the real error
let initResult = Promise.resolve();

export function initPush() {
  if (!CONFIGURED) return;
  initResult = withOneSignal((OneSignal) =>
    OneSignal.init({ appId: APP_ID, allowLocalhostAsSecureOrigin: true })
  );
  initResult.catch(console.error);
}

// Link this browser to our user id, so the backend can send to "external_id = user.id"
export function linkPushToUser(userId) {
  if (!CONFIGURED) return;
  withOneSignal((OneSignal) => OneSignal.login(String(userId))).catch(console.error);
}

// Ask the browser for permission and subscribe
export async function enablePush() {
  if (!CONFIGURED) {
    throw new Error(
      "Web Push is not set up yet: put your OneSignal App ID in frontend/.env (VITE_ONESIGNAL_APP_ID) and restart the frontend."
    );
  }
  try {
    await initResult;
  } catch (error) {
    // e.g. "Can only be used on: https://..." -> Site URL in OneSignal doesn't match this site
    throw new Error(`OneSignal could not start: ${error.message}. Check the Site URL in OneSignal settings.`);
  }
  return withOneSignal(async (OneSignal) => {
    await OneSignal.Notifications.requestPermission();
    await OneSignal.User.PushSubscription.optIn();
    return OneSignal.User.PushSubscription.optedIn;
  });
}

export function isPushEnabled() {
  if (!CONFIGURED) return Promise.resolve(false);
  return withOneSignal((OneSignal) => OneSignal.User.PushSubscription.optedIn);
}
