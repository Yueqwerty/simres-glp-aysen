/**
 * Badge component - shadcn/ui
 * Componente para mostrar badges/etiquetas
 */

import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-slate-900 text-slate-50 hover:bg-slate-900/80",
        secondary:
          "border-transparent bg-slate-100 text-slate-900 hover:bg-slate-100/80",
        success:
          "border-transparent bg-green-100 text-green-800 hover:bg-green-100/80",
        warning:
          "border-transparent bg-yellow-100 text-yellow-800 hover:bg-yellow-100/80",
        danger:
          "border-transparent bg-red-100 text-red-800 hover:bg-red-100/80",
        outline: "text-slate-700 border-slate-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}
