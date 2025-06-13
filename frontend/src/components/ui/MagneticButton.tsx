import { motion } from "framer-motion";
import { ReactNode } from "react";

export const MagneticButton = ({ children }: { children: ReactNode }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className="relative overflow-hidden group"
    >
      <motion.span 
        className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        initial={{ x: -100, y: -100 }}
      />
      <span className="relative z-10">{children}</span>
    </motion.button>
  );
};
