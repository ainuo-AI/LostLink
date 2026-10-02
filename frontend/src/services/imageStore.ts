/**
 * 图片本地存储服务
 *
 * IndexedDB 适合保存 Blob；localStorage 只适合少量字符串数据。
 * 页面只拿到 demo-image 开头的编号，通过本模块统一增、查、删图片。
 */
const DB_NAME = 'lostlink-demo-images-v1'
const STORE_NAME = 'images'

function openImageDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!('indexedDB' in window)) {
      reject(new Error('当前浏览器不支持图片本地保存。'))
      return
    }
    const request = window.indexedDB.open(DB_NAME, 1)
    request.onupgradeneeded = () => request.result.createObjectStore(STORE_NAME)
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(new Error('无法打开图片存储，请检查浏览器存储权限。'))
    request.onblocked = () => reject(new Error('图片存储被其他页面占用，请关闭其他标签页后重试。'))
  })
}

/**
 * 封装一次 IndexedDB 事务：调用者只描述对 object store 的操作，
 * 本函数统一负责连接关闭和错误信息，避免每个增删查函数重复代码。
 */
async function transact<T>(mode: IDBTransactionMode, operation: (store: IDBObjectStore, finish: (value: T) => void) => void): Promise<T> {
  const db = await openImageDatabase()
  return new Promise<T>((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, mode)
    let value: T
    transaction.oncomplete = () => { db.close(); resolve(value) }
    transaction.onerror = () => { db.close(); reject(new Error('图片保存或读取失败，请重试。')) }
    transaction.onabort = () => { db.close(); reject(new Error('图片操作被取消，请重试。')) }
    operation(transaction.objectStore(STORE_NAME), (result) => { value = result })
  })
}

/** 保存图片 Blob 并返回可放进表单草稿的本地编号。 */
export async function saveImage(file: File): Promise<string> {
  const id = `demo-image-${crypto.randomUUID()}`
  await transact<void>('readwrite', (store) => { store.put(file, id) })
  return id
}

/** 根据编号读取图片；编号不存在或内容不是 Blob 时返回 null。 */
export async function readImage(id: string): Promise<Blob | null> {
  return transact<Blob | null>('readonly', (store, finish) => {
    const request = store.get(id)
    request.onsuccess = () => finish(request.result instanceof Blob ? request.result : null)
  })
}

/** 删除用户移除或重置表单时不再需要的图片。 */
export async function removeImage(id: string): Promise<void> {
  await transact<void>('readwrite', (store) => { store.delete(id) })
}
