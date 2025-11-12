import { useParams } from 'react-router-dom'

export default function JobDetail() {
  const { id } = useParams()
  return (
    <div>
      <h2>Job Detail: {id}</h2>
      <p>Coming soon: live logs and assets.</p>
    </div>
  )
}
