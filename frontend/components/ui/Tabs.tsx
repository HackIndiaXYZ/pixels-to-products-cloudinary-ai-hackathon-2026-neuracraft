import { ReactNode, useState } from 'react'
import clsx from 'clsx'

interface Tab {
  id: string
  label: string
  content: ReactNode
}

interface TabsProps {
  tabs: Tab[]
  defaultTab?: string
}

export default function Tabs({ tabs, defaultTab }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id)
  
  return (
    <div>
      <div className="border-b border-border">
        <div className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'pb-3 px-1 text-sm font-medium border-b-2 transition-colors duration-200',
                activeTab === tab.id
                  ? 'border-primary-500 text-text-primary'
                  : 'border-transparent text-text-tertiary hover:text-text-secondary'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-6">
        {tabs.find(tab => tab.id === activeTab)?.content}
      </div>
    </div>
  )
}
