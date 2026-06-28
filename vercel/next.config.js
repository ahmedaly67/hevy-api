/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    HEVY_ACCESS_TOKEN: process.env.HEVY_ACCESS_TOKEN || "",
    HEVY_USER_ID: process.env.HEVY_USER_ID || "",
    HEVY_REFRESH_TOKEN: process.env.HEVY_REFRESH_TOKEN || "",
    HEVY_TOKENS: process.env.HEVY_TOKENS || "",
  },
};

module.exports = nextConfig;
