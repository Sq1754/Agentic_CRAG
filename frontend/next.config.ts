import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow HMR from local network IPs (e.g. when accessing dev server from another device)
  allowedDevOrigins: ["192.168.153.1", "192.168.1.0/24"],
};

export default nextConfig;
