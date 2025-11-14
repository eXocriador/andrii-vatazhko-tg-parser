import { Schema, model, type InferSchemaType, type Model } from 'mongoose';

const postSchema = new Schema(
  {
    tg_id: { type: Number, required: true, unique: true },
    type: { type: String, enum: ['fundraising', 'report'], required: true },
    text: { type: String, required: true },
    images: { type: [String], default: [] },
    links: { type: [String], default: [] },
    date: { type: Date, required: true },
  },
  {
    timestamps: true,
  },
);

postSchema.index({ date: -1 });

export type PostDocument = InferSchemaType<typeof postSchema>;

export const PostModel: Model<PostDocument> = model<PostDocument>('Post', postSchema);
