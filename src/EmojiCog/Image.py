import time

import cv2
import discord


class Image:
    imageState = None
    emojiDim = 128

    attachment: discord.Attachment

    def __init__(self, attachment, name, interpolation=cv2.INTER_AREA):
        self.attachment = attachment
        self.file_name = name
        self.pathed_name = f"images/{name}_proposed_{time.time()}_{interpolation}"
        self.is_attachment_downloaded = False
        self.cv2_mat = None
        self.interpolation = interpolation

    async def force_scale_to_emoji_size(self):
        await self.downscale_internal(self.emojiDim, self.emojiDim)

    async def downscale_ideal(self):
        width, height = self.get_squarified_resize_dimensions(self.attachment.width, self.attachment.height)
        await self.downscale_internal(width, height)

    async def download_attachment(self, force=False):
        return cv2.imdecode(await self.attachment.read(), -1)
        # if not self.is_attachment_downloaded or force:
        #     self.is_attachment_downloaded = True

    def get_bytes(self):
        is_success, im_buf_arr = cv2.imencode(".png", self.cv2_mat)
        return im_buf_arr.tobytes()

    async def downscale_internal(self, width, height):
        img = await self.download_attachment()
        self.cv2_mat = cv2.resize(img, (width, height), interpolation=self.interpolation)
        cv2.imwrite(self.pathed_name + ".png", self.cv2_mat)

    def get_squarified_resize_dimensions(self, width, height):
        if width == height:
            width = self.emojiDim
            height = self.emojiDim
        elif width > height:
            ratio = height / width
            height = int(self.emojiDim * ratio)
            width = self.emojiDim
        else:
            ratio = width / height
            width = int(self.emojiDim * ratio)
            height = self.emojiDim
        return width, height
