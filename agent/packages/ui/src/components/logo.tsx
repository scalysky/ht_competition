import { type ComponentProps } from "solid-js"

export const Mark = (props: { class?: string }) => {
  return (
    <svg
      data-component="logo-mark"
      classList={{ [props.class ?? ""]: !!props.class }}
      viewBox="0 0 16 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect data-slot="logo-mark-bar-weak" x="1" y="11" width="3.5" height="8" rx="1" fill="var(--icon-weak-base)" />
      <rect data-slot="logo-mark-bar-base" x="6.25" y="7" width="3.5" height="12" rx="1" fill="var(--icon-base)" />
      <rect data-slot="logo-mark-bar-strong" x="11.5" y="3" width="3.5" height="16" rx="1" fill="var(--icon-strong-base)" />
    </svg>
  )
}

export const Splash = (props: Pick<ComponentProps<"svg">, "ref" | "class">) => {
  return (
    <svg
      ref={props.ref}
      data-component="logo-splash"
      classList={{ [props.class ?? ""]: !!props.class }}
      viewBox="0 0 80 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="5" y="55" width="17.5" height="40" rx="5" fill="var(--icon-weak-base)" />
      <rect x="31.25" y="35" width="17.5" height="60" rx="5" fill="var(--icon-base)" />
      <rect x="57.5" y="15" width="17.5" height="80" rx="5" fill="var(--icon-strong-base)" />
    </svg>
  )
}

export const Logo = (props: { class?: string }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 268 42"
      fill="none"
      classList={{ [props.class ?? ""]: !!props.class }}
    >
      <g>
        <rect x="0" y="25" width="5" height="8" rx="1" fill="var(--icon-weak-base)" />
        <rect x="7.5" y="21" width="5" height="12" rx="1" fill="var(--icon-base)" />
        <rect x="15" y="17" width="5" height="16" rx="1" fill="var(--icon-strong-base)" />
        <text
          x="30"
          y="31"
          font-family="system-ui, -apple-system, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif"
          font-size="22"
          font-weight="700"
          letter-spacing="1"
          fill="var(--icon-strong-base)"
        >
          华泰金融数据Agent
        </text>
      </g>
    </svg>
  )
}
