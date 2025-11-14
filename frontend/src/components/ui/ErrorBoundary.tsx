import { Component, ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { hasError: boolean; error?: any }

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: any) {
    return { hasError: true, error }
  }

  componentDidCatch(error: any, info: any) {
    // eslint-disable-next-line no-console
    console.error('Logs page error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="card">
          <div className="text-base font-semibold">Something went wrong</div>
          <div className="text-sm text-muted mt-1">The Logs page failed to render. Please refresh the page or restart the dev server.</div>
          {this.state.error ? (
            <pre className="mt-3 text-xs bg-white/5 border border-white/10 p-3 rounded-lg overflow-auto">
              {String(this.state.error)}
            </pre>
          ) : null}
        </div>
      )
    }
    return this.props.children
  }
}
