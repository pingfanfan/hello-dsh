import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'hello-plugin'
export const inject = ['tools']

export function apply(ctx: Context) {
  ctx.tools.register(defineTool({
    name: 'pingfan_hello',
    description: '返回一句固定问候，用于验证第三方插件是否加载成功。',
    parameters: {
      who: { type: 'string', description: '要问候的对象' },
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          greeting: { type: 'string', required: true },
        },
      },
      render: (_args, value) => [{ type: 'text', text: value.greeting }],
    },
    execute(args) {
      const who = args.who ?? 'world'
      return Promise.resolve({ greeting: `HELLO_FROM_PINGFAN_PLUGIN to ${who}` })
    },
  }))
}
