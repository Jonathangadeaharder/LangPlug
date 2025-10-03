// Type declarations for @heroicons/react
declare module '@heroicons/react/24/solid' {
  import { ComponentType, SVGProps } from 'react'

  type HeroIcon = ComponentType<SVGProps<SVGSVGElement> & { className?: string }>

  export const PlayIcon: HeroIcon
  export const PauseIcon: HeroIcon
  export const SpeakerWaveIcon: HeroIcon
  export const SpeakerXMarkIcon: HeroIcon
  export const CheckCircleIcon: HeroIcon
  export const ArrowLeftIcon: HeroIcon
  export const ExclamationTriangleIcon: HeroIcon
  export const ClockIcon: HeroIcon
  export const CheckIcon: HeroIcon
  export const XMarkIcon: HeroIcon
  export const ChevronDownIcon: HeroIcon
  export const ChevronUpIcon: HeroIcon
  export const ChevronRightIcon: HeroIcon
  export const MagnifyingGlassIcon: HeroIcon
  export const HeartIcon: HeroIcon
  export const StarIcon: HeroIcon
  export const EyeIcon: HeroIcon
  export const EyeSlashIcon: HeroIcon
  export const PlusIcon: HeroIcon
  export const MinusIcon: HeroIcon
  export const ForwardIcon: HeroIcon
  export const LanguageIcon: HeroIcon
  export const ArrowPathIcon: HeroIcon
}

declare module '@heroicons/react/24/outline' {
  import { ComponentType, SVGProps } from 'react'

  export interface HeroIcon extends ComponentType<SVGProps<SVGSVGElement>> {}

  export const PlayIcon: HeroIcon
  export const PauseIcon: HeroIcon
  export const SpeakerWaveIcon: HeroIcon
  export const SpeakerXMarkIcon: HeroIcon
  export const CheckCircleIcon: HeroIcon
  export const ArrowLeftIcon: HeroIcon
  export const ExclamationTriangleIcon: HeroIcon
  export const ClockIcon: HeroIcon
  export const CheckIcon: HeroIcon
  export const XMarkIcon: HeroIcon

  // Add more icons as needed
  const Icons: Record<string, HeroIcon>
  export = Icons
}
