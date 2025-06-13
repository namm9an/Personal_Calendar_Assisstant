"use client";

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Input } from '@/components/ui/input';

interface FloatingLabelInputProps
  extends Omit<React.ComponentProps<typeof Input>, 'id'> {
  label: string;
  id: string;
}

export const FloatingLabelInput = ({
  label,
  id,
  value,
  onBlur,
  ...props
}: FloatingLabelInputProps) => {
  const [isFocused, setIsFocused] = React.useState(false);
  const hasValue = value ? String(value).length > 0 : false;

  const isFloating = isFocused || hasValue;

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(true);
    props.onFocus?.(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    onBlur?.(e);
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
        className="h-12 pt-4 text-white bg-black/20 backdrop-blur-lg border border-white/20 rounded-lg transition-colors duration-300 focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-0 disabled:opacity-50"
        {...props}
      />
    </div>
  );
};
