import { Modal, Steps, Result, Spin } from 'antd'
import { LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import styles from './index.module.scss'

export interface CollectionResult {
  success: boolean
  message: string
  news_collected: number
  bidding_collected: number
  errors: string[]
}

interface CollectionModalProps {
  open: boolean
  collecting: boolean
  result: CollectionResult | null
  industryName: string
  onClose: () => void
}

export default function CollectionModal({
  open,
  collecting,
  result,
  industryName,
  onClose,
}: CollectionModalProps) {
  // 计算当前步骤
  const getCurrentStep = () => {
    if (!collecting && !result) return 0
    if (collecting) return 1
    if (result) return 2
    return 0
  }

  const currentStep = getCurrentStep()

  // 步骤状态
  const getStepStatus = (step: number): 'wait' | 'process' | 'finish' | 'error' => {
    if (step < currentStep) return 'finish'
    if (step === currentStep) {
      if (step === 2 && result && !result.success) return 'error'
      return 'process'
    }
    return 'wait'
  }

  return (
    <Modal
      title={`采集数据 - ${industryName}`}
      open={open}
      footer={null}
      closable={!collecting}
      maskClosable={false}
      keyboard={false}
      onCancel={onClose}
      width={500}
      centered
    >
      <div className={styles.container}>
        <Steps
          direction="vertical"
          current={currentStep}
          items={[
            {
              title: '准备采集',
              description: '初始化采集任务',
              status: getStepStatus(0),
              icon: currentStep === 0 ? <LoadingOutlined /> : <CheckCircleOutlined />,
            },
            {
              title: '正在采集',
              description: collecting ? (
                <div className={styles.collecting}>
                  <Spin size="small" />
                  <span>正在从多个数据源获取最新信息...</span>
                </div>
              ) : (
                '从多个数据源获取数据'
              ),
              status: getStepStatus(1),
              icon: collecting ? <LoadingOutlined spin /> :
                    currentStep > 1 ? <CheckCircleOutlined /> : undefined,
            },
            {
              title: '采集完成',
              description: result ? (
                result.success ? '数据已更新' : '部分数据采集失败'
              ) : (
                '等待采集结果'
              ),
              status: getStepStatus(2),
              icon: result ? (
                result.success ? <CheckCircleOutlined /> : <CloseCircleOutlined />
              ) : undefined,
            },
          ]}
        />

        {/* 采集结果 */}
        {result && (
          <div className={styles.result}>
            <Result
              status={result.success ? 'success' : 'warning'}
              title={result.success ? '采集完成' : '采集完成（部分失败）'}
              subTitle={
                <div className={styles.stats}>
                  <p>行业资讯：<strong>{result.news_collected}</strong> 条</p>
                  <p>招投标信息：<strong>{result.bidding_collected}</strong> 条</p>
                  {result.errors.length > 0 && (
                    <div className={styles.errors}>
                      <p>错误信息：</p>
                      <ul>
                        {result.errors.slice(0, 3).map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                        {result.errors.length > 3 && (
                          <li>...还有 {result.errors.length - 3} 个错误</li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              }
              extra={
                <button className={styles.closeBtn} onClick={onClose}>
                  关闭
                </button>
              }
            />
          </div>
        )}
      </div>
    </Modal>
  )
}
