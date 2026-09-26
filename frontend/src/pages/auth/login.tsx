import * as api from '@/api'
import { authActions } from '@/store/auth'
import { LockOutlined, MailOutlined, UserOutlined } from '@ant-design/icons'
import { Button, Form, Input, message } from 'antd'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import styles from './login.module.scss'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const [isLogin, setIsLogin] = useState(true)

  const from = (location.state as any)?.from?.pathname || '/chat'

  const onLogin = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const { data } = await api.auth.login(values)
      authActions.login(data.access_token, data.user)
      message.success('登录成功')
      navigate(from, { replace: true })
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  const onRegister = async (values: {
    username: string
    email: string
    password: string
    confirmPassword: string
  }) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }

    setLoading(true)
    try {
      const { data } = await api.auth.register({
        username: values.username,
        email: values.email,
        password: values.password,
      })
      authActions.login(data.access_token, data.user)
      message.success('注册成功')
      navigate(from, { replace: true })
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles['login-page']}>
      <div className={styles['login-container']}>
        {/* 左侧品牌区域 */}
        <div className={styles['brand-section']}>
          <div className={styles['brand-content']}>
            <div className={styles['brand-icon']}>
              <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M24 4L4 14V34L24 44L44 34V14L24 4Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
                <path d="M24 4V24M24 24L4 14M24 24L44 14M24 24V44" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
              </svg>
            </div>
            <h1 className={styles['brand-title']}>行业信息助手</h1>
            <p className={styles['brand-subtitle']}>Intelligence Assistant</p>
            <div className={styles['brand-features']}>
              <div className={styles['feature-item']}>
                <span className={styles['feature-icon']} />
                <span>AI 驱动的深度研究</span>
              </div>
              <div className={styles['feature-item']}>
                <span className={styles['feature-icon']} />
                <span>多维度数据分析</span>
              </div>
              <div className={styles['feature-item']}>
                <span className={styles['feature-icon']} />
                <span>智能报告生成</span>
              </div>
            </div>
          </div>
        </div>

        {/* 右侧表单区域 */}
        <div className={styles['form-section']}>
          <div className={styles['form-container']}>
            <div className={styles['form-header']}>
              <h2>{isLogin ? '欢迎回来' : '创建账户'}</h2>
              <p>{isLogin ? '登录您的账户以继续' : '注册新账户开始使用'}</p>
            </div>

            {isLogin ? (
              <Form
                name="login"
                onFinish={onLogin}
                autoComplete="off"
                layout="vertical"
                requiredMark={false}
              >
                <Form.Item
                  name="username"
                  rules={[{ required: true, message: '请输入用户名' }]}
                >
                  <Input
                    prefix={<UserOutlined className={styles['input-icon']} />}
                    placeholder="用户名或邮箱"
                    size="large"
                    className={styles['form-input']}
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[{ required: true, message: '请输入密码' }]}
                >
                  <Input.Password
                    prefix={<LockOutlined className={styles['input-icon']} />}
                    placeholder="密码"
                    size="large"
                    className={styles['form-input']}
                  />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    block
                    size="large"
                    className={styles['submit-btn']}
                  >
                    登录
                  </Button>
                </Form.Item>
              </Form>
            ) : (
              <Form
                name="register"
                onFinish={onRegister}
                autoComplete="off"
                layout="vertical"
                requiredMark={false}
              >
                <Form.Item
                  name="username"
                  rules={[
                    { required: true, message: '请输入用户名' },
                    { min: 3, message: '用户名至少3个字符' },
                  ]}
                >
                  <Input
                    prefix={<UserOutlined className={styles['input-icon']} />}
                    placeholder="用户名"
                    size="large"
                    className={styles['form-input']}
                  />
                </Form.Item>

                <Form.Item
                  name="email"
                  rules={[
                    { required: true, message: '请输入邮箱' },
                    { type: 'email', message: '请输入有效的邮箱地址' },
                  ]}
                >
                  <Input
                    prefix={<MailOutlined className={styles['input-icon']} />}
                    placeholder="邮箱"
                    size="large"
                    className={styles['form-input']}
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[
                    { required: true, message: '请输入密码' },
                    { min: 6, message: '密码至少6个字符' },
                  ]}
                >
                  <Input.Password
                    prefix={<LockOutlined className={styles['input-icon']} />}
                    placeholder="密码"
                    size="large"
                    className={styles['form-input']}
                  />
                </Form.Item>

                <Form.Item
                  name="confirmPassword"
                  rules={[{ required: true, message: '请确认密码' }]}
                >
                  <Input.Password
                    prefix={<LockOutlined className={styles['input-icon']} />}
                    placeholder="确认密码"
                    size="large"
                    className={styles['form-input']}
                  />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    block
                    size="large"
                    className={styles['submit-btn']}
                  >
                    注册
                  </Button>
                </Form.Item>
              </Form>
            )}

            <div className={styles['form-footer']}>
              <span className={styles['switch-text']}>
                {isLogin ? '还没有账户？' : '已有账户？'}
              </span>
              <button
                type="button"
                className={styles['switch-btn']}
                onClick={() => setIsLogin(!isLogin)}
              >
                {isLogin ? '立即注册' : '返回登录'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
