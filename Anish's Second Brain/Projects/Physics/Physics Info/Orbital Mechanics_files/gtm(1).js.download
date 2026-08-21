/* How to set up a test server for GA4:
 * Check the company drive for documentation
 * AoPS - Development > AoPS & Academy Development > Documentation > Google Analytics
 * Unused / Old Google IDs for reference:
 *
 * 01-19-21
 * AoPS Main Analytics Property: UA-1905305-1 (Ditched in favor of GA4) - ARogers
 *
 * 09-17-2019 - These should not be used anywhere to my knowledge - AReilly
 *
 * AoPS Tag Manager Test Analytics Property: UA-1905305-5
 * AoPS - Community Users Filtered Out Property: UA-1905305-6
 */

/* Initialize the Data Layer First */
window.dataLayer = window.dataLayer || [];

(function (w, d, s, l, i) {
	w[l] = w[l] || [];
	w[l].push({"gtm.start": new Date().getTime(), event: "gtm.js"});
	var f = d.getElementsByTagName(s)[0],
		j = d.createElement(s),
		dl = l !== "dataLayer" ? "&l=" + l : "";
	j.async = true;
	j.src = "https://www.googletagmanager.com/gtm.js?id=" + i + dl;
	f.parentNode.insertBefore(j, f);
})(window, document, "script", "dataLayer", AoPS.bd.ga.GTM_container);

function gtag() {
	window.dataLayer.push(arguments);
}
gtag("js", new Date());

/* GA4 Measurement ID from Account -> Property -> Data Stream on GA */
gtag("config", AoPS.bd.ga.ga4);

/* ID of GTM Container */
gtag("config", AoPS.bd.ga.GTM_container, {
	custom_map: {
		dimension1: "logged_in",
		dimension2: "user_type",
	},
});
gtag("set", "user_properties", {
	logged_in: AoPS.bd.user_info.logged_in,
	user_type: AoPS.bd.user_info.user_type,
});
