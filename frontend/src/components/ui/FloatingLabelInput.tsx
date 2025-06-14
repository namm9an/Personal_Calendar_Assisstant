"use client";

import * as React from 'react';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

const MotionLabel = motion.label;

interface FloatingLabelInputProps
  extends Omit<React.ComponentProps<typeof Input>, 'id'> {
  label: string;
  id: string;
  labelClassName?: string;
  inputClassName?: string;
}

export const FloatingLabelInput: React.FC<FloatingLabelInputProps> = ({
  id,
  label,
  value,
  onChange,
  type = "text",
  className = "",
  labelClassName = "",
  inputClassName = "",
  onFocus,
  onBlur,
  ...props
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [hasValue, setHasValue] = useState(value !== "" && value !== undefined);

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(true);
    if (onFocus) onFocus(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    if (onBlur) onBlur(e);
  };

  useEffect(() => {
    setHasValue(value !== "" && value !== undefined);
  }, [value]);

  const labelVariants = {
    initial: {
      y: "50%",
      scale: 1,
      opacity: 0.7,
      color: "#a3b3c6", // lighter color for better visibility
    },
    focused: {
      y: "-60%",
      scale: 0.85,
      opacity: 1,
      color: "rgb(var(--primary))", // primary color
    },
  };

  return (
    <div className={cn("relative w-full", className)}>
      <MotionLabel
        htmlFor={id}
        className={cn(
          "absolute left-3 transform -translate-y-1/2 pointer-events-none text-white/80",
          "transition-all duration-200 ease-in-out origin-[0] z-10",
          labelClassName
        )}
        variants={labelVariants}
        initial="initial"
        animate={isFocused || hasValue ? "focused" : "initial"}
        transition={{ duration: 0.2 }}
      >
        {label}
      </MotionLabel>
      <Input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        className={cn(
          "h-14 pt-4 glass-input", // Using our updated glass-input utility class
          "focus:ring-2 focus:ring-primary focus:border-primary", // Primary color focus
          "placeholder:text-neutral-400", // Placeholder color
          inputClassName
        )}
        {...props}
      />
    </div>
  );
};
