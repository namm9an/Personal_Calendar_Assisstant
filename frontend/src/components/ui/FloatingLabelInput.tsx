"use client";

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Input, InputProps } from '@/components/ui/input';

interface FloatingLabelInputProps extends InputProps {
  label: string;
  id: string;
}

export const FloatingLabelInput = ({ label, id, ...props }: FloatingLabelInputProps) => {
  const [isFocused, setIsFocused] = useState(false);
  const [hasValue, setHasValue] = useState(props.value ? String(props.value).length > 0 : false);

  const isFloating = isFocused || hasValue;

  const handleFocus = () => setIsFocused(true);
  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    setHasValue(e.target.value.length > 0);
    if (props.onBlur) {
      props.onBlur(e);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setHasValue(e.target.value.length > 0);
    if (props.onChange) {
      props.onChange(e);
    }
  };

  return (
    <div className="relative">
      <motion.label
        htmlFor={id}
        className="absolute left-3 text-neutral-400 pointer-events-none"
        initial={{ y: '50%', x: 0, scale: 1 }}
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
        onFocus={handleFocus}
        onBlur={handleBlur}
        onChange={handleChange}
        className="bg-white/5 border-white/20 backdrop-blur-sm h-12 pt-4 focus-visible:ring-offset-0 focus-visible:ring-2 focus-visible:ring-accent"
        {...props}
      />
    </div>
  );
};
