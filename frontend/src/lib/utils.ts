import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Standard utility function to merge Tailwind classes cleanly.
 * Built by our frontend team to make class combining easy and conflict-free.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
