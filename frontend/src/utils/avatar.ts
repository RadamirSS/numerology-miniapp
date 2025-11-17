// Утилиты для работы с аватаром

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const MAX_DIMENSION = 512;

/**
 * Сжимает изображение до указанного размера
 */
export function compressImage(file: File, maxWidth: number = MAX_DIMENSION, maxHeight: number = MAX_DIMENSION): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const img = new Image();
      
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;
        
        // Вычисляем новые размеры с сохранением пропорций
        if (width > height) {
          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }
        } else {
          if (height > maxHeight) {
            width = (width * maxHeight) / height;
            height = maxHeight;
          }
        }
        
        canvas.width = width;
        canvas.height = height;
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Не удалось создать контекст canvas'));
          return;
        }
        
        ctx.drawImage(img, 0, 0, width, height);
        
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob);
            } else {
              reject(new Error('Не удалось сжать изображение'));
            }
          },
          'image/jpeg',
          0.85 // качество JPEG
        );
      };
      
      img.onerror = () => reject(new Error('Ошибка загрузки изображения'));
      img.src = e.target?.result as string;
    };
    
    reader.onerror = () => reject(new Error('Ошибка чтения файла'));
    reader.readAsDataURL(file);
  });
}

/**
 * Валидирует файл изображения
 */
export function validateImageFile(file: File): { valid: boolean; error?: string } {
  // Проверка типа файла
  if (!file.type.startsWith('image/')) {
    return { valid: false, error: 'Файл должен быть изображением' };
  }
  
  // Проверка размера
  if (file.size > MAX_FILE_SIZE) {
    return { valid: false, error: `Размер файла не должен превышать ${MAX_FILE_SIZE / 1024 / 1024}MB` };
  }
  
  return { valid: true };
}

/**
 * Конвертирует Blob в base64 строку
 */
export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result as string;
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/**
 * Обрабатывает выбранный файл: валидирует, сжимает и возвращает base64
 */
export async function processAvatarFile(file: File): Promise<string> {
  const validation = validateImageFile(file);
  if (!validation.valid) {
    throw new Error(validation.error);
  }
  
  const compressed = await compressImage(file);
  const base64 = await blobToBase64(compressed);
  
  return base64;
}

