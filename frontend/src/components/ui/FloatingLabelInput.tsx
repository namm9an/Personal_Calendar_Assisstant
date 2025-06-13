"use client";

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Input, InputProps } from '@/components/ui/input';

interface FloatingLabelInputProps extends Omit<InputProps, 'id'> {
  label: string;
  id: string;
}

export const FloatingLabelInput = ({ label, id, value, onBlur, ...props }: FloatingLabelInputProps) => {
  const [isFocused, setIsFocused] = useState(false);
  const hasValue = value ? String(value).length > 0 : false;

  const isFloating = isFocused || hasValue;

  const handleFocus = () => setIsFocused(true);
  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    if (onBlur) {
      onBlur(e);
    }
  };

  return (
    <div className="relative">
      <motion.label
        htmlFor={id}
        className="absolute left-3 text-neutral-400 pointer-events-none"
        initial={false}
        animate={{
          y: isFloating ? '-90%' : '50%',
          x: isFloating ? -5 : 0,
          scale: isFloating ? 0.85 : 1,
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        style={{ transformOrigin: 'left' }}
      >
        {label}
      </motion.label>
      <Input
        id={id}
        value={value}
        onFocus={handleFocus}
        onBlur={handleBlur}
        className="bg-white/5 border-white/20 backdrop-blur-sm h-12 pt-4 focus-visible:ring-offset-0 focus-visible:ring-2 focus-visible:ring-accent"
        {...props}
      />
    </div>
  );
};
