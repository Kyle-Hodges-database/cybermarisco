(() => {
    const originalFetch = window.fetch;
    window.fetch = async function (resource, config = {}) {
        resource
        const url = resource.toString();
        const isAllowed = url.includes("/api/v2/authentication-transaction");

        if (isAllowed) {
            console.log('Injecting');
            config.headers = {
                ...config.headers,
                "x-obg-trusted-traffic": "1",
                "x-obg-country-code": "ES",
                "x-obg-origin": "ES",
                "x-obg-internal": "1",
            };
        } else {
            console.log(`Ignoring: ${url}`)
        }

        return originalFetch(resource, config);
    };
})();