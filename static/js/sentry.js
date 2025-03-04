Sentry.onLoad(function() {
    // Check if Sentry should be enabled
    if (window.SENTRY_ENABLED === false) {
        console.log('Sentry is disabled');
        return;
    }

    console.log('Initializing Sentry...');
    Sentry.init({
        // Tracing
        tracesSampleRate: 1.0, // Capture 100% of the transactions
        // Session Replay
        replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
        replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
    });
    console.log('Sentry initialized successfully');
})