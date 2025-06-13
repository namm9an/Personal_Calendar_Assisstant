'use client';

import { ReactNode } from "react";

export const MagneticButton = ({ children }: { children: ReactNode }) => {
  return (
    <button
      className="relative overflow-hidden group p-4 rounded-lg bg-white/10 backdrop-blur-lg hover:bg-white/20 transition-all duration-300"
    >
      <span className="relative z-10 flex items-center gap-2">{children}</span>
    </button>
  );
};
