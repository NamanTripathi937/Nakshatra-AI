type JsonLdProps = {
  data: Record<string, unknown> | Array<Record<string, unknown>>
  id?: string
}

function serializeJsonLd(data: JsonLdProps["data"]) {
  return JSON.stringify(data).replace(/</g, "\\u003c")
}

export default function JsonLd({ data, id }: JsonLdProps) {
  return (
    <script
      id={id}
      type="application/ld+json"
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: serializeJsonLd(data) }}
    />
  )
}
