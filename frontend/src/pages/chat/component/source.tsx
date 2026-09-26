import styles from './source.module.scss'

export default function Source(props: {
  list: API.ChatItem['search_results']
}) {
  const { list } = props

  return (
    <div className={styles['source__list']}>
      {list?.map((source) => (
        <a
          className={styles['source__item']}
          key={source.id}
          href={source.url}
          target="_blank"
        >
          <img className={styles['icon']} src={source.siteIcon} />
          <div className={styles['info']}>
            <span className={styles['host']}>{source.host}</span>
            <span className={styles['name']} title={source.name}>
              {source.name}
            </span>
          </div>
        </a>
      ))}
    </div>
  )
}
