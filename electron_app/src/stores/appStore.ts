import { defineStore } from 'pinia';

export interface ChatItem {
  title: string;
  icon: string;
  key: string; // 对应视图类型：llmModel/soulModel/imgModel/vidolModel
  timestamp?: string;
}

export interface Message {
  role: 'user' | 'system' | 'assistant';
  content: string;
  // 【新增】为了精准定位消息，需要给 Message 添加唯一 id 属性（关键）
  id?: string;
}

export interface HistoryItem {
  id: string;
  title: string;
  icon: string;
  list: Message[];
}

// 定义应用状态类型
interface AppState {
  apiUrl: string; // API 请求地址
  llmModel: string; // LLM 模型名称
  system_prompt: string; // 系统提示语
  currentView: string; // 当前激活的视图key
  currentHistoryId: string | null;
  chatList: ChatItem[];
  historyList: HistoryItem[];
}

export const useAppStore = defineStore('app', {
  state: (): AppState => ({
    apiUrl: 'http://127.0.0.1:8000/api/v1/chat/completions',
    llmModel: 'llama3.2:3b',
    system_prompt: '答案要简洁明了，直奔主题，避免冗长的解释。',
    currentView: 'llmModel', // 默认显示聊天视图
    currentHistoryId: '1',
    chatList: [
      { title: "新对话", icon: "fa-comments", key: "llmModel" },
      { title: "语音生成", icon: "fa-microphone", key: "soulModel" },
      { title: "图像生成", icon: "fa-picture-o", key: "imgModel" },
      { title: "视频生成", icon: "fa-film", key: "vidolModel" }
    ],
    historyList: [
      { 
        id: "1", 
        title: "技术文档总结", 
        icon: "fa-file-text-o",
        list: [
          { id: "1-1", role: "user", content: "请帮我总结一下这份技术文档的主要内容和关键点。" },
          { id: "1-2", role: "assistant", content: "这份技术文档主要介绍了XYZ技术的架构设计、核心功能和应用场景。关键点包括高可扩展性、低延迟处理和多平台支持。文档还提供了详细的API说明和使用示例，帮助开发者快速上手。" }
        ]
      },
      { 
        id: "2", 
        title: "Python 编程问题", 
        icon: "fa-code",
        list: [
          { id: "2-1", role: "user", content: "如何在Python中实现单例模式？" },
          { id: "2-2", role: "assistant", content: "在Python中实现单例模式有多种方法，最常见的是使用装饰器、元类或模块级别的实现。其中元类方法是最Pythonic的方式，通过重写__call__方法控制实例创建。" },
          { id: "2-3", role: "user", content: "能给我一个示例代码吗？" },
          { id: "2-4", role: "assistant", content: "当然可以，这是一个使用元类实现单例模式的示例：\n\nclass SingletonMeta(type):\n    _instances = {}\n    def __call__(cls, *args, **kwargs):\n        if cls not in cls._instances:\n            cls._instances[cls] = super().__call__(*args, **kwargs)\n        return cls._instances[cls]" }
        ]
      },
      { 
        id: "3", 
        title: "知识库查询测试", 
        icon: "fa-search", 
        list: [
          { id: "3-1", role: "user", content: "什么是Pinia？" },
          { id: "3-2", role: "assistant", content: "Pinia是Vue.js的状态管理库，是Vuex的继任者。它提供了更简洁的API，更好的TypeScript支持，以及更灵活的状态管理方式。" },
          { id: "3-3", role: "user", content: "它和Vuex有什么主要区别？" },
          { id: "3-4", role: "assistant", content: "Pinia与Vuex的主要区别包括：没有Mutation，直接通过Action修改状态；更好的TypeScript集成；不需要嵌套模块，可以平级组织store；支持组合式API风格等。" }
        ]
      }
    ]
  }),
  getters: {
    // 获取当前选中的历史记录
    getCurrentHistory: (state) => {
      return state.historyList.find(item => item.id === state.currentHistoryId) || state.historyList[0] || null;
    }
  },
  actions: {
    // 切换视图
    switchView(key: string) {
      this.currentView = key;
    },
    // 设置当前选中的历史记录
    setCurrentHistoryId(id: string) {
      this.currentHistoryId = id;
      // 切换到聊天视图
      this.switchView('llmModel');
    },
    // 添加新的历史记录
    addHistory(history: HistoryItem) {
      this.historyList.unshift(history);
      // 设置新对话为当前选中的历史记录
      this.setCurrentHistoryId(history.id);
    },
    // 更新历史记录
    updateHistory(id: string, updates: Partial<HistoryItem>) {
      const index = this.historyList.findIndex(item => item.id === id);
      if (index !== -1) {
        this.historyList[index] = { ...this.historyList[index], ...updates };
      }
    },
    // 追加消息到历史记录
    appendMessageToHistory(id: string, message: Message): string {
      const index = this.historyList.findIndex(item => item.id === id);
      if (index !== -1) {
        this.historyList[index].list.push(message);
        // 自动更新历史记录标题的逻辑（保留）
        if (message.role === 'user' && this.historyList[index].title === '新对话') {
          this.historyList[index].title = message.content.slice(0, 20) + (message.content.length > 20 ? '...' : '');
        }
  
        // 核心：返回消息的 id（优先用消息自带的 id，无则生成唯一 id 并补充）
        if (message.id) {
          return message.id;
        } else {
          // 生成唯一 id（时间戳 + 随机字符串，避免重复）
          const uniqueId = Date.now() + '-' + Math.random().toString(36).slice(2, 8);
          // 给消息补充 id（更新数组中的消息对象）
          this.historyList[index].list[this.historyList[index].list.length - 1].id = uniqueId;
          return uniqueId;
        }
      }
      // 若未找到历史记录，返回空字符串（兜底）
      return '';
    },
    // 【新增】更新历史记录中某一条消息的内容
    updateMessageContent(historyId: string, messageId: string, content: string) {
      // 1. 找到对应的历史记录
      const historyIndex = this.historyList.findIndex(item => item.id === historyId);
      if (historyIndex === -1) return;

      // 2. 找到对应的消息
      const messageIndex = this.historyList[historyIndex].list.findIndex(item => item.id === messageId);
      if (messageIndex === -1) return;

      // 3. 更新消息内容（核心逻辑）
      this.historyList[historyIndex].list[messageIndex].content = content;
    }
  }
});