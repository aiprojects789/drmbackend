import React, { useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE;
const PAYPAL_CLIENT_ID = import.meta.env.VITE_PAYPAL_CLIENT_ID;

function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) return resolve();
    const s = document.createElement("script");
    s.src = src;
    s.onload = resolve;
    s.onerror = reject;
    document.body.appendChild(s);
  });
}

export default function PayPalButton({ amount = "10.00" }) {
  useEffect(() => {
    const sdkUrl = `https://www.paypal.com/sdk/js?client-id=${PAYPAL_CLIENT_ID}&currency=USD`;

    loadScript(sdkUrl)
      .then(() => {
        if (!window.paypal) return;

        window.paypal
          .Buttons({
            // Create order by calling backend
            createOrder: function () {
              return fetch(`${API_BASE}/create-order`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ amount }),
              })
                .then((res) => res.json())
                .then((data) => data.id);
            },

            // Capture order on approval
            onApprove: function (data) {
              return fetch(`${API_BASE}/capture-order/${data.orderID}`, {
                method: "POST",
              })
                .then((res) => res.json())
                .then((details) => {
                  console.log("✅ Capture:", details);
                  alert("Payment successful!");
                });
            },

            onError: function (err) {
              console.error("❌ PayPal Error:", err);
              alert("Payment failed. Please try again.");
            },
          })
          .render("#paypal-button-container");
      })
      .catch(console.error);
  }, [amount]);

  return <div id="paypal-button-container" />;
}
