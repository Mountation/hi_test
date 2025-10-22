import React, { useEffect, useState } from 'react'
import api from '../utils/api'
import { List, Card } from 'antd'

type User = { id: number; email: string; full_name?: string }

export default function Users() {
  const [users, setUsers] = useState<User[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/users/');
        setUsers(res.data);
      } catch (_e) { setUsers([]); }
    };
    load();
  }, [])

  return (
    <div>
      <h2>Users</h2>
      <Card>
        <List dataSource={users} renderItem={u => (
          <List.Item key={u.id}>{u.email} - {u.full_name}</List.Item>
        )} />
      </Card>
    </div>
  )
}
