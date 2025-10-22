import React, { useEffect, useState } from 'react'
import api from '../utils/api'
import { List, Card } from 'antd'

type Item = { id: number; name: string; description?: string }

export default function Items() {
  const [items, setItems] = useState<Item[]>([])

  useEffect(() => {
    const load = async () => {
      try { const res = await api.get('/items/'); setItems(res.data); } catch (_e) { setItems([]); }
    };
    load();
  }, [])

  return (
    <div>
      <h2>Items</h2>
      <Card>
        <List dataSource={items} renderItem={it => (
          <List.Item key={it.id}>{it.name} - {it.description}</List.Item>
        )} />
      </Card>
    </div>
  )
}
