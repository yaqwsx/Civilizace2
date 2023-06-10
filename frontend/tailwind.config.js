module.exports = {
    important: true,
    content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
    darkMode: false, // or 'media' or 'class'
    theme: {
        screens: {
            sm: "640px",
            md: "768px",
            lg: "1024px",
            xl: "1280px",
            // "2xl": "1536px",
        },
        extend: {},
    },
    safelist: [
        {
            pattern: /bg-(\w+)-(\d)00/,
            variants: ["hover", "focus"],
        },
    ],
    variants: {
        extend: {},
    },
    plugins: [],
};
