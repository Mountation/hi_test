import React, { useEffect, useState } from 'react'
import api from '../utils/api'
import { Card } from 'antd'

type User = { id: number; email: string; full_name?: string }

export default function Me() {
  const [me, setMe] = useState<User | null>(null)

  useEffect(() => {
    const load = async () => {
      try { const res = await api.get('/users/me'); setMe(res.data); } catch (_e) { setMe(null); }
    };
    load();
  }, [])

  if (!me) return <Card><h2>Me</h2><p>Not authenticated or no data.</p></Card>

  return (
    <Card>
      <h2>Me</h2>
      <p>{me.email}</p>
      <p>{me.full_name}</p>
    </Card>
  )
}
