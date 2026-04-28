/**
 * Lightweight inline SVG icon components — replaces react-icons.
 * Fixes Rollup 4 / Vite 5 scope-binding build error.
 */
const Icon = ({ d, size = 20, stroke = 'currentColor', fill = 'none', strokeWidth = 2, ...rest }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        {...rest}
    >
        <path d={d} />
    </svg>
)

export const IconArrowRight = (p) => <Icon {...p} d="M5 12h14M12 5l7 7-7 7" />
export const IconStar = (p) => <Icon {...p} fill="currentColor" stroke="none" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
export const IconSearch = (p) => <Icon {...p} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
export const IconFilter = (p) => <Icon {...p} d="M4 6h16M7 12h10M10 18h4" />
export const IconMapPin = (p) => <Icon {...p} d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0zM12 10a1 1 0 1 0 0 2 1 1 0 0 0 0-2z" />
export const IconDollarSign = (p) => <Icon {...p} d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
export const IconHeart = (p) => <Icon {...p} d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
export const IconUser = (p) => <Icon {...p} d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" />
export const IconThumbsUp = (p) => <Icon {...p} d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
export const IconThumbsDown = (p) => <Icon {...p} d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
export const IconRefreshCw = (p) => <Icon {...p} d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
export const IconInfo = (p) => <Icon {...p} d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 8h.01M11 12h1v4h1" />
export const IconShield = (p) => <Icon {...p} d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
export const IconZap = (p) => <Icon {...p} d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
export const IconTrendingUp = (p) => <Icon {...p} d="M23 6l-9.5 9.5-5-5L1 18M17 6h6v6" />
export const IconTarget = (p) => <Icon {...p} d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12zM12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" />
export const IconAward = (p) => <Icon {...p} d="M12 15a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM8.21 13.89L7 23l5-3 5 3-1.21-9.12" />
export const IconSend = (p) => <Icon {...p} d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
export const IconBot = (p) => <Icon {...p} d="M12 2a2 2 0 0 1 2 2v2h4a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4V4a2 2 0 0 1 2-2zM8 12H8.01M16 12H16.01" />
export const IconX = (p) => <Icon {...p} d="M18 6L6 18M6 6l12 12" />
export const IconMessageCircle = (p) => <Icon {...p} d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
export const IconMenu = (p) => <Icon {...p} d="M3 12h18M3 6h18M3 18h18" />
export const IconBrain = (p) => <Icon {...p} d="M9.5 2a2.5 2.5 0 0 1 5 0v1a7 7 0 0 1 7 7v1a7 7 0 0 1-7 7v1a2.5 2.5 0 0 1-5 0v-1a7 7 0 0 1-7-7v-1a7 7 0 0 1 7-7V2z" />
export const IconMap = (p) => <Icon {...p} d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4zM8 2v16M16 6v16" />
export const IconGlobe = (p) => <Icon {...p} d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />

export default Icon
